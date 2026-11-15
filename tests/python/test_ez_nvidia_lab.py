"""Hermetic tests for ez_nvidia_lab (no Comfy, no GPU, no network, no subprocess).

Every branch of ``custom_nodes/ez_nvidia_lab/nodes.py`` is exercised here: the
stdlib catalog reader over good and malformed documents, the four nodes through
their fail-soft paths, the injectable ``SubprocessRunner`` double, and the
``EZ_NVIDIA_LAB_CATALOG`` override. Nothing spawns a process or consults the
host PATH unless the test asks for it.
"""

from __future__ import annotations

import ast
import builtins
import json
import platform
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_nvidia_lab  # noqa: E402
from ez_nvidia_lab import nodes  # noqa: E402
from ez_nvidia_lab.nodes import (  # noqa: E402
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
    CatalogError,
    EZNvidiaLabCatalog,
    EZNvidiaLabJob,
    EZNvidiaLabPreflight,
    EZNvidiaLabVerdict,
    artifact_ref_reason,
    catalog_path,
    find_tool,
    job_command,
    load_catalog,
    parse_catalog,
    preflight_report,
    render_catalog,
)

PACK_DIR = ROOT / "custom_nodes" / "ez_nvidia_lab"
PACK_SOURCE = PACK_DIR / "nodes.py"

# Module-scope imports the pack is allowed to make (stdlib only).
ALLOWED_IMPORTS: frozenset[str] = frozenset(
    {
        "__future__",
        "collections.abc",
        "json",
        "os",
        "pathlib",
        "platform",
        "re",
        "shutil",
        "subprocess",
        "sys",
        "typing",
    }
)

# Code points the repo-wide ASCII guard forbids (mirrors the committed set).
FORBIDDEN_CODEPOINTS: frozenset[int] = frozenset(
    {
        0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212,
        0x02BC, 0x02BB, 0x2018, 0x2019, 0x201A, 0x201B, 0x201C, 0x201D,
        0x201E, 0x201F, 0x2026, 0x2022, 0x00B7, 0x00A0, 0x2007, 0x2009,
        0x202F, 0x00D7, 0x00F7, 0x00B1, 0x2248, 0x2260, 0x2261, 0x2264,
        0x2265, 0x2190, 0x2191, 0x2192, 0x2193, 0x2194, 0x00B2, 0x00B3,
    }
)

LONG_LICENSE = (
    "NVIDIA Internal Scientific Research and Development Model License with a "
    "long tail that the table view has to clip"
)


class FakeProc:
    """``CompletedProc`` double for the injectable runner."""

    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        """Store the canned result.

        Args:
            returncode: Exit code the fake reports.
            stdout: Captured stdout.
            stderr: Captured stderr.
        """
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeRunner:
    """``SubprocessRunner`` double that records argv instead of spawning."""

    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "",
        stderr: str = "",
        error: OSError | None = None,
    ) -> None:
        """Store the canned result.

        Args:
            returncode: Exit code to report.
            stdout: Captured stdout to report.
            stderr: Captured stderr to report.
            error: When set, the call raises it instead of returning.
        """
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.error = error
        self.calls: list[tuple[list[str], dict[str, bool]]] = []

    def __call__(
        self, argv: list[str], *, check: bool, capture_output: bool, text: bool
    ) -> FakeProc:
        """Record ``argv`` and report the canned result.

        Args:
            argv: Command vector.
            check: Forwarded check flag.
            capture_output: Forwarded capture flag.
            text: Forwarded text flag.

        Returns:
            The canned :class:`FakeProc`.

        Raises:
            OSError: When the test asked the runner to fail to start.
        """
        if self.error is not None:
            raise self.error
        self.calls.append(
            (argv, {"check": check, "capture_output": capture_output, "text": text})
        )
        return FakeProc(self.returncode, self.stdout, self.stderr)


def _tool(**overrides: object) -> dict[str, object]:
    """One fully valid catalog row, with ``overrides`` applied.

    Args:
        **overrides: Fields to replace (``id`` also rewrites ``graph``).

    Returns:
        A row document.
    """
    row: dict[str, object] = {
        "id": "artifixer",
        "title": "ArtiFixer",
        "status": "opt-in",
        "task": "Repair a scene.",
        "input": "a capture",
        "output": "novel views",
        "upstream": "https://example.test/artifixer",
        "see_also": [],
        "code_license": "Apache-2.0",
        "weights_license": "NVIDIA Open Model License",
        "commercial_use": "permitted",
        "weights": [
            {
                "source": "huggingface",
                "repo": "nvidia/ArtiFixer",
                "file": "artifixer.pt",
                "gb": 6.4,
                "gated": False,
            }
        ],
        "artifact": "container-image",
        "artifact_ref": "ghcr.io/nv-tlabs/artifixer:tag",
        "arm64": "published",
        "gb10": "unverified",
        "install": "docker-pull",
        "cmd": "",
        "vram_gb": 40,
        "disk_gb": 120,
        "comfy_shape": "host-cli",
        "nodes": ["EZNvidiaLabPreflight", "EZNvidiaLabJob"],
        "graph": "labs/nvidia/artifixer",
        "app": {
            "mode": "splat-repair",
            "occupancy": "none",
            "deliverable": "repaired views",
        },
        "gate_notes": "n/a - this row is installable.",
        "reopen": "n/a - this row is installable.",
        "verify": "bazelisk test //tests:bats_nvidia_lab_test",
        "sources": ["https://example.test/artifixer"],
    }
    row.update(overrides)
    if "graph" not in overrides and "id" in overrides:
        row["graph"] = f"labs/nvidia/{overrides['id']}"
    return row


def _weight(**overrides: object) -> dict[str, object]:
    """One fully valid weight entry, with ``overrides`` applied.

    Args:
        **overrides: Fields to replace on the default entry.

    Returns:
        A weight document.
    """
    row: dict[str, object] = {
        "source": "huggingface",
        "repo": "nvidia/ArtiFixer",
        "file": "artifixer.pt",
        "gb": 6.4,
        "gated": False,
    }
    row.update(overrides)
    return row


def _doc(*tools: dict[str, object]) -> dict[str, object]:
    """A fully valid catalog document.

    Args:
        *tools: Rows to include; none means one default row.

    Returns:
        A catalog document.
    """
    return {
        "schema": 1,
        "tier": "nvidia-lab",
        "tier_title": "NVIDIA lab",
        "updated": "2026-11-15",
        "status_values": list(nodes.STATUS_VALUES),
        "commercial_values": list(nodes.COMMERCIAL_VALUES),
        "arm64_values": list(nodes.ARM64_VALUES),
        "artifact_values": list(nodes.ARTIFACT_VALUES),
        "comfy_shape_values": list(nodes.COMFY_SHAPE_VALUES),
        "tools": list(tools) if tools else [_tool()],
    }


def _write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, document: object
) -> Path:
    """Write ``document`` (dict or raw text) and point the pack at it.

    Args:
        tmp_path: Test directory.
        monkeypatch: Fixture used for the env override.
        document: Document to serialize, or raw text.

    Returns:
        The catalog path.
    """
    path = tmp_path / "catalog.json"
    text = document if isinstance(document, str) else json.dumps(document)
    path.write_text(str(text), encoding="utf-8")
    monkeypatch.setenv(nodes.CATALOG_ENV, str(path))
    return path


def _row(**overrides: object) -> nodes.ToolRow:
    """One validated row built from the fixture document.

    Args:
        **overrides: Fields to replace on the default row.

    Returns:
        A validated row.
    """
    return parse_catalog(json.dumps(_doc(_tool(**overrides))))["tools"][0]


def _ready(row: nodes.ToolRow) -> tuple[str, bool]:
    """Preflight ``row`` with both host probes faked to succeed.

    Args:
        row: Validated row.

    Returns:
        ``(report, ok)`` from :func:`preflight_report`.
    """
    return preflight_report(
        row, path_lookup=lambda name: f"/usr/bin/{name}", machine=lambda: "aarch64"
    )


def _block_ez_common(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``ez_common`` unimportable for one test.

    Args:
        monkeypatch: Fixture used to restore the real import hook.
    """
    real_import = builtins.__import__

    def _guarded(name: str, *args: object, **kwargs: object) -> object:
        """Refuse ``ez_common`` the way a bare host does.

        Args:
            name: Module name.
            *args: Forwarded to the real import.
            **kwargs: Forwarded to the real import.

        Returns:
            Whatever the real import returns.

        Raises:
            ImportError: When ``ez_common`` is asked for.
        """
        if name == "ez_common" or name.startswith("ez_common."):
            raise ImportError("no ez_common here")
        forwarded_args: tuple[Any, ...] = args
        forwarded_kwargs: dict[str, Any] = kwargs
        return real_import(name, *forwarded_args, **forwarded_kwargs)

    monkeypatch.setattr(builtins, "__import__", _guarded)


# --------------------------------------------------------------------------- #
# Pack shape: auto-loaded by every boot, so import must stay stdlib-only
# --------------------------------------------------------------------------- #


def test_pack_exports_and_shape() -> None:
    assert set(NODE_CLASS_MAPPINGS) == {
        "EZNvidiaLabCatalog",
        "EZNvidiaLabPreflight",
        "EZNvidiaLabJob",
        "EZNvidiaLabVerdict",
    }
    assert set(NODE_DISPLAY_NAME_MAPPINGS) == set(NODE_CLASS_MAPPINGS)
    assert ez_nvidia_lab.NODE_CLASS_MAPPINGS is NODE_CLASS_MAPPINGS
    assert ez_nvidia_lab.NODE_DISPLAY_NAME_MAPPINGS is NODE_DISPLAY_NAME_MAPPINGS
    assert not hasattr(ez_nvidia_lab, "WEB_DIRECTORY")
    assert not hasattr(ez_nvidia_lab, "register_routes")
    node_classes = (
        EZNvidiaLabCatalog,
        EZNvidiaLabPreflight,
        EZNvidiaLabJob,
        EZNvidiaLabVerdict,
    )
    assert tuple(NODE_CLASS_MAPPINGS.values()) == node_classes
    for cls in node_classes:
        assert cls.CATEGORY == "EZ Comfy/NVIDIA Lab"
        assert cls.FUNCTION == "run"
        assert cls.RETURN_NAMES and len(cls.RETURN_NAMES) == len(cls.RETURN_TYPES)
        assert cls.DESCRIPTION.isascii()


def test_output_nodes_are_the_catalog_and_the_verdict() -> None:
    assert NODE_CLASS_MAPPINGS["EZNvidiaLabCatalog"] is EZNvidiaLabCatalog
    assert NODE_CLASS_MAPPINGS["EZNvidiaLabVerdict"] is EZNvidiaLabVerdict
    assert EZNvidiaLabCatalog.OUTPUT_NODE is True
    assert EZNvidiaLabVerdict.OUTPUT_NODE is True
    assert not hasattr(NODE_CLASS_MAPPINGS["EZNvidiaLabPreflight"], "OUTPUT_NODE")
    assert not hasattr(NODE_CLASS_MAPPINGS["EZNvidiaLabJob"], "OUTPUT_NODE")


def test_module_scope_imports_are_stdlib_only() -> None:
    tree = ast.parse(PACK_SOURCE.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            seen.update(alias.name for alias in statement.names)
        elif isinstance(statement, ast.ImportFrom):
            assert statement.module is not None
            seen.add(statement.module)
    assert seen <= ALLOWED_IMPORTS, sorted(seen - ALLOWED_IMPORTS)


def test_sibling_pack_is_only_imported_inside_functions() -> None:
    tree = ast.parse(PACK_SOURCE.read_text(encoding="utf-8"))
    assert "ez_common" in _all_import_names(tree)
    for forbidden in ("torch", "numpy", "comfy", "nvidia_lab", "requests"):
        assert forbidden not in _all_import_names(tree)
    for statement in ast.walk(tree):
        if not isinstance(statement, ast.ImportFrom) or statement.module is None:
            continue
        module = statement.module
        if module.startswith("ez_common"):
            assert statement.col_offset > 0, f"{module} imported at module scope"


def _all_import_names(tree: ast.Module) -> set[str]:
    """Every module name the file imports anywhere.

    Args:
        tree: Parsed module.

    Returns:
        Module names from Import and ImportFrom nodes.
    """
    names: set[str] = set()
    for statement in ast.walk(tree):
        if isinstance(statement, ast.Import):
            names.update(alias.name for alias in statement.names)
        elif isinstance(statement, ast.ImportFrom) and statement.module:
            names.add(statement.module)
    return names


def test_new_files_are_ascii_only() -> None:
    for path in (PACK_DIR / "nodes.py", PACK_DIR / "__init__.py", Path(__file__)):
        text = path.read_text(encoding="utf-8")
        assert text.isascii(), path.name
        for code in FORBIDDEN_CODEPOINTS:
            assert chr(code) not in text, f"{path.name} U+{code:04X}"


# --------------------------------------------------------------------------- #
# Catalog reader: env override, good documents, and every fail-closed rule
# --------------------------------------------------------------------------- #


def test_catalog_path_env_override_and_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(nodes.CATALOG_ENV, raising=False)
    assert catalog_path() == nodes.DEFAULT_CATALOG_PATH
    monkeypatch.setenv(nodes.CATALOG_ENV, "   ")
    assert catalog_path() == nodes.DEFAULT_CATALOG_PATH
    monkeypatch.setenv(nodes.CATALOG_ENV, str(tmp_path / "other.json"))
    assert catalog_path() == tmp_path / "other.json"


def test_reader_accepts_the_committed_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(nodes.CATALOG_ENV, raising=False)
    catalog = load_catalog()
    assert catalog["tier"] == "nvidia-lab"
    assert len(catalog["tools"]) >= 10
    assert find_tool(catalog, "artifixer") is not None
    assert find_tool(catalog, "nope") is None


def test_reader_missing_file_is_a_catalog_error(tmp_path: Path) -> None:
    with pytest.raises(CatalogError, match="cannot read"):
        load_catalog(tmp_path / "absent" / "catalog.json")


@pytest.mark.parametrize("text", ["not json", "[]", '{"schema": 1', '"a string"'])
def test_parser_rejects_bad_top_levels(text: str) -> None:
    with pytest.raises(CatalogError):
        parse_catalog(text)


@pytest.mark.parametrize(
    ("key", "value", "needle"),
    [
        ("schema", 2, "schema: expected 1"),
        ("schema", True, "schema: expected an integer"),
        ("schema", "1", "schema: expected an integer"),
        ("tier", "other", "tier: expected"),
        ("updated", "15-11-2026", "updated: expected YYYY"),
        ("tools", {}, "tools: expected an array"),
        ("tools", ["x"], r"tools\[0\]: expected an object"),
        ("status_values", ["opt-in"], "status_values"),
        ("arm64_values", "published", "arm64_values"),
        ("comfy_shape_values", [1], "comfy_shape_values"),
    ],
)
def test_reader_fails_closed_on_the_top_level(
    key: str, value: object, needle: str
) -> None:
    document = _doc()
    document[key] = value
    with pytest.raises(CatalogError, match=needle):
        parse_catalog(json.dumps(document))


def test_reader_rejects_a_missing_and_an_unknown_top_key() -> None:
    document = _doc()
    del document["tier_title"]
    with pytest.raises(CatalogError, match="tier_title: missing"):
        parse_catalog(json.dumps(document))
    document = _doc()
    document["extra"] = 1
    with pytest.raises(CatalogError, match="extra: unknown key"):
        parse_catalog(json.dumps(document))


def test_reader_rejects_duplicate_row_ids() -> None:
    with pytest.raises(CatalogError, match="duplicate id"):
        parse_catalog(json.dumps(_doc(_tool(), _tool())))


@pytest.mark.parametrize(
    ("overrides", "needle"),
    [
        ({"id": "Bad_Id"}, "id: expected kebab-case"),
        ({"nodes": ["EZNvidiaLabGhost"]}, "unknown node class"),
        ({"nodes": "EZNvidiaLabJob"}, "nodes: expected an array"),
        ({"nodes": [1]}, "nodes: expected only strings"),
        ({"graph": "labs/nvidia/other"}, "graph: expected"),
        ({"status": "maybe"}, "status: expected one of"),
        ({"commercial_use": "free"}, "commercial_use: expected one of"),
        ({"arm64": "sort-of"}, "arm64: expected one of"),
        ({"artifact": "tarball"}, "artifact: expected one of"),
        ({"gb10": "hopeful"}, "gb10: expected one of"),
        ({"install": "scp"}, "install: expected one of"),
        ({"comfy_shape": "cluster"}, "comfy_shape: expected one of"),
        ({"vram_gb": "40"}, "vram_gb: expected an integer"),
        ({"vram_gb": True}, "vram_gb: expected an integer"),
        ({"disk_gb": 1.5}, "disk_gb: expected an integer"),
        ({"title": 3}, "title: expected a string"),
        ({"cmd": None}, "cmd: expected a string"),
        ({"see_also": {}}, "see_also: expected an array"),
        ({"sources": ["ok", 2]}, "sources: expected only strings"),
    ],
)
def test_reader_fails_closed_on_a_row(
    overrides: dict[str, object], needle: str
) -> None:
    with pytest.raises(CatalogError, match=needle):
        parse_catalog(json.dumps(_doc(_tool(**overrides))))


def test_reader_rejects_row_key_drift() -> None:
    row = _tool()
    row["notes"] = "extra"
    with pytest.raises(CatalogError, match="notes: unknown key"):
        parse_catalog(json.dumps(_doc(row)))
    row = _tool()
    del row["gate_notes"]
    with pytest.raises(CatalogError, match="gate_notes: missing"):
        parse_catalog(json.dumps(_doc(row)))


@pytest.mark.parametrize(
    ("field", "value", "needle"),
    [
        ("weights", {}, "weights: expected an array"),
        ("weights", ["x"], r"weights\[0\]: expected an object"),
        (
            "weights",
            [{"source": "h", "repo": "r", "file": "f", "gb": 1, "gated": "yes"}],
            "gated: expected a boolean",
        ),
        (
            "weights",
            [{"source": "h", "repo": "r", "file": "f", "gb": 1, "gated": 0}],
            "gated: expected a boolean",
        ),
        (
            "weights",
            [{"source": "h", "repo": "r", "file": "f", "gb": "big", "gated": True}],
            "gb: expected a number",
        ),
        (
            "weights",
            [{"source": "h", "repo": "r", "file": "f", "gb": True, "gated": True}],
            "gb: expected a number",
        ),
        (
            "weights",
            [{"source": "h", "repo": "r", "gb": 1.0, "gated": True}],
            "file: missing",
        ),
        ("app", [], "app: expected an object"),
        ("app", {"mode": "m", "occupancy": "wan", "deliverable": "d"}, "occupancy"),
        (
            "app",
            {"mode": "m", "occupancy": "nope", "deliverable": "d"},
            "occupancy: expected one of",
        ),
        ("app", {"mode": "m", "deliverable": "d"}, "occupancy: missing"),
    ],
)
def test_reader_fails_closed_on_nested_records(
    field: str, value: object, needle: str
) -> None:
    with pytest.raises(CatalogError, match=needle):
        parse_catalog(json.dumps(_doc(_tool(**{field: value}))))


def test_reader_accepts_an_empty_weights_list() -> None:
    catalog = parse_catalog(json.dumps(_doc(_tool(weights=[]))))
    assert catalog["tools"][0]["weights"] == []


def test_reader_accepts_null_as_unchecked_gating() -> None:
    """Null is a gating state of its own, not the claim that a repo is open."""
    catalog = parse_catalog(json.dumps(_doc(_tool(weights=[_weight(gated=None)]))))
    assert catalog["tools"][0]["weights"][0]["gated"] is None


def test_reader_reads_an_integer_weight_as_a_float() -> None:
    catalog = parse_catalog(
        json.dumps(
            _doc(
                _tool(
                    weights=[
                        {"source": "h", "repo": "r", "file": "f", "gb": 3, "gated": False}
                    ]
                )
            )
        )
    )
    assert catalog["tools"][0]["weights"][0]["gb"] == 3.0


# --------------------------------------------------------------------------- #
# artifact_ref_reason: no network, just the shape of the ref
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("install", "artifact", "ref", "expected"),
    [
        ("none", "paper-only", "", ""),
        ("git-clone", "source-build", "", "needs an artifact_ref"),
        ("git-clone", "source-build", "https://a b/c.git", "contains whitespace"),
        ("docker-pull", "container-image", "nvcr.io/nvidia/nre", ""),
        ("docker-pull", "container-image", "nvidia-nre", "not a registry/repo"),
        ("git-clone", "source-build", "github.com/a/b.git", "not a URL to fetch"),
        ("git-clone", "source-build", "https://github.com/a/b.git", ""),
    ],
)
def test_artifact_ref_reason(
    install: str, artifact: str, ref: str, expected: str
) -> None:
    reason = artifact_ref_reason(_row(install=install, artifact=artifact, artifact_ref=ref))
    if expected:
        assert expected in reason
    else:
        assert reason == ""


# --------------------------------------------------------------------------- #
# Catalog node
# --------------------------------------------------------------------------- #


def test_catalog_node_table_and_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(
        tmp_path,
        monkeypatch,
        _doc(
            _tool(),
            _tool(
                id="lyra-two",
                title="Project Lyra 2.0",
                status="blocked-license",
                weights_license=LONG_LICENSE,
                commercial_use="non-commercial",
                weights=[],
                install="none",
                artifact="source-build",
                artifact_ref="",
            ),
        ),
    )
    table = EZNvidiaLabCatalog().run("table")["result"][0]
    assert "NVIDIA lab - 2 rows" in table
    assert "artifixer" in table and "lyra-two" in table
    assert LONG_LICENSE[:20] in table and LONG_LICENSE not in table

    listing = EZNvidiaLabCatalog().run(" list ")["result"][0]
    assert "status: opt-in" in listing
    assert f"weights license: {LONG_LICENSE}" in listing
    assert "weights: 0 entries" in listing
    assert "commercial use: non-commercial" in listing


@pytest.mark.parametrize(
    ("value", "expected"),
    [(40, "40 GB vram"), (0, f"vram {nodes.NOT_PUBLISHED}")],
)
def test_footprint_field(value: int, expected: str) -> None:
    assert nodes._footprint_field(value, "vram") == expected


def test_catalog_node_list_marks_an_unpublished_footprint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A row whose footprint is 0 says no figure is published, not 0 GB."""
    _write(
        tmp_path,
        monkeypatch,
        _doc(_tool(), _tool(id="sizeless", vram_gb=0, disk_gb=0)),
    )
    listing = EZNvidiaLabCatalog().run("list")["result"][0]
    assert "footprint: 40 GB vram, 120 GB disk" in listing
    assert (
        f"footprint: vram {nodes.NOT_PUBLISHED}, disk {nodes.NOT_PUBLISHED}" in listing
    )
    assert "footprint: 0" not in listing


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1.5, "1.5 GB"), (2.0, "2 GB"), (0, nodes.NOT_PUBLISHED)],
)
def test_weight_size_field(value: float, expected: str) -> None:
    assert nodes._weight_size_field(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("artifixer.pt", "artifixer.pt"),
        ("checkpoints/", f"{nodes.TREE_MARK}checkpoints/"),
        ("S8-F*-R*/*.distcp", f"{nodes.SHARD_MARK}S8-F*-R*/*.distcp"),
        ("model-0000*-of-00005.safetensors", "shards: model-0000*-of-00005.safetensors"),
    ],
)
def test_weight_file_field(value: str, expected: str) -> None:
    assert nodes._weight_file_field(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(True, "gated"), (False, "ungated"), (None, nodes.GATING_NOT_CHECKED)],
)
def test_weight_gating_field(value: bool | None, expected: str) -> None:
    assert nodes._weight_gating_field(value) == expected


def test_weights_field_names_every_shape_per_weight() -> None:
    """One part per weight, each naming its shape, size, and gating state."""
    row = _row(
        weights=[
            _weight(file="checkpoints/", gb=82.3),
            _weight(file="S8-F*-R*/*.distcp", gb=121.6),
            _weight(file="small.pt", gb=0, gated=None),
        ]
    )
    assert nodes._weights_field(row["weights"]) == (
        "3 entries: nvidia/ArtiFixer/tree: checkpoints/ (82.3 GB, ungated); "
        "nvidia/ArtiFixer/shards: S8-F*-R*/*.distcp (121.6 GB, ungated); "
        f"nvidia/ArtiFixer/small.pt ({nodes.NOT_PUBLISHED}, {nodes.GATING_NOT_CHECKED})"
    )


def test_weights_field_counts_one_entry_and_an_empty_row() -> None:
    assert nodes._weights_field([]) == "0 entries"
    row = _row(weights=[_weight(gated=True)])
    assert nodes._weights_field(row["weights"]) == (
        "1 entry: nvidia/ArtiFixer/artifixer.pt (6.4 GB, gated)"
    )


def test_catalog_node_list_shares_the_page_wording(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The card a node prints reads like the card the generated page prints."""
    _write(
        tmp_path,
        monkeypatch,
        _doc(
            _tool(
                weights=[
                    _weight(file="luxdit_image/", gb=23.5),
                    _weight(file="base_model.pt", gb=28.95, gated=True),
                ]
            )
        ),
    )
    listing = EZNvidiaLabCatalog().run("list")["result"][0]
    assert (
        "weights: 2 entries: nvidia/ArtiFixer/tree: luxdit_image/ (23.5 GB, ungated); "
        "nvidia/ArtiFixer/base_model.pt (28.95 GB, gated)" in listing
    )


def test_catalog_node_list_prints_the_measured_cosmos_row() -> None:
    """The shipped card calls the gated 28.95 GB repo gated, never ungated."""
    catalog = load_catalog(nodes.DEFAULT_CATALOG_PATH)
    row = next(tool for tool in catalog["tools"] if tool["id"] == "cosmos-drive-dreams")
    assert nodes._weights_field(row["weights"]) == (
        "1 entry: nvidia/Cosmos-Transfer1-7B-Sample-AV/base_model.pt "
        "(28.95 GB, gated)"
    )


def test_catalog_node_empty_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = _doc()
    document["tools"] = []
    _write(tmp_path, monkeypatch, document)
    report = EZNvidiaLabCatalog().run("table")["result"][0]
    assert "(no rows)" in report
    assert render_catalog(load_catalog(), detail="table") == report


def test_catalog_node_rejects_a_bad_detail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, _doc())
    report = EZNvidiaLabCatalog().run("yaml")["result"][0]
    assert "detail must be one of" in report


def test_catalog_node_degrades_on_a_malformed_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write(tmp_path, monkeypatch, "{oops")
    report = EZNvidiaLabCatalog().run("table")["result"][0]
    assert "malformed JSON" in report
    path.unlink()
    report = EZNvidiaLabCatalog().run("table")["result"][0]
    assert "cannot read" in report


def test_catalog_node_input_types() -> None:
    spec = EZNvidiaLabCatalog.INPUT_TYPES()
    assert spec["required"]["detail"][0] == ["list", "table"]
    assert spec["required"]["detail"][1]["default"] == "table"


# --------------------------------------------------------------------------- #
# Preflight
# --------------------------------------------------------------------------- #


def test_preflight_reports_ready_on_aarch64_with_docker() -> None:
    report, ok = _ready(_row())
    assert ok is True
    assert "verdict: ready" in report
    assert "docker at /usr/bin/docker" in report
    assert "note: no GB10 run reported upstream yet" in report
    assert "artifact: container-image ref ghcr.io" in report


def test_preflight_blocks_a_non_opt_in_row() -> None:
    report, ok = _ready(_row(status="deferred"))
    assert ok is False
    assert "not an install path" in report


def test_preflight_blocks_a_missing_binary() -> None:
    report, ok = preflight_report(
        _row(), path_lookup=lambda _name: None, machine=lambda: "aarch64"
    )
    assert ok is False
    assert "docker is not on PATH" in report


def test_preflight_blocks_a_pip_install_row_without_pip() -> None:
    report, ok = preflight_report(
        _row(install="pip-install", artifact="host-cli", artifact_ref="tool"),
        path_lookup=lambda _name: None,
        machine=lambda: "aarch64",
    )
    assert ok is False
    assert "pip is not on PATH" in report


def test_preflight_blocks_a_foreign_arch_and_unsupported_gb10() -> None:
    report, ok = preflight_report(
        _row(gb10="unsupported"),
        path_lookup=lambda name: f"/usr/bin/{name}",
        machine=lambda: "x86_64",
    )
    assert ok is False
    assert "the host reports 'x86_64'" in report
    assert "unsupported on GB10" in report


def test_preflight_accepts_a_verified_gb10_and_no_install_verb() -> None:
    report, ok = preflight_report(
        _row(gb10="verified", install="none", artifact_ref=""),
        path_lookup=lambda _name: None,
        machine=lambda: "aarch64",
    )
    assert ok is True
    assert "no external tool needed" in report
    assert "note:" not in report


def test_preflight_flags_a_broken_artifact_ref() -> None:
    report, ok = _ready(_row(artifact_ref=""))
    assert ok is False
    assert "needs an artifact_ref" in report
    assert "ref (none)" in report


def test_preflight_node_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, monkeypatch, _doc(_tool()))
    node = EZNvidiaLabPreflight(
        path_lookup=lambda name: f"/usr/bin/{name}", machine=lambda: "aarch64"
    )
    report, ok = node.run(" artifixer ")
    assert ok is True and report.startswith("preflight artifixer")

    report, ok = node.run("ghost")
    assert ok is False and "no catalog row with id 'ghost'" in report

    report, ok = node.run("   ")
    assert ok is False and "widget tool_id is empty" in report

    _write(tmp_path, monkeypatch, "{oops")
    report, ok = node.run("artifixer")
    assert ok is False and "malformed JSON" in report


def test_preflight_node_defaults_to_the_real_host_probes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, _doc(_tool(install="none", artifact_ref="")))
    report, ok = EZNvidiaLabPreflight().run("artifixer")
    assert isinstance(ok, bool)
    assert f"host: {platform.machine()}" in report
    assert "no external tool needed" in report


def test_preflight_input_types() -> None:
    spec = EZNvidiaLabPreflight.INPUT_TYPES()
    assert spec["required"]["tool_id"][0] == "STRING"


# --------------------------------------------------------------------------- #
# Job node
# --------------------------------------------------------------------------- #


def test_job_command_shape() -> None:
    argv = job_command(Path("/opt/manage.sh"), "artifixer", "/in/scene.zip", '{"n":1}')
    assert argv == [
        "/opt/manage.sh",
        "nvidia-lab",
        "run",
        "artifixer",
        "--input",
        "/in/scene.zip",
        "--params",
        '{"n":1}',
    ]


def _input_file(tmp_path: Path) -> str:
    """Create an input file and return its path as text.

    Args:
        tmp_path: Test directory.

    Returns:
        Path to a small file.
    """
    source = tmp_path / "capture.zip"
    source.write_text("capture", encoding="utf-8")
    return str(source)


def test_job_runs_an_opt_in_row_through_the_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, _doc(_tool()))
    runner = FakeRunner(stdout="done\n", stderr="warning: slow\n")
    source = _input_file(tmp_path)
    job = EZNvidiaLabJob(runner=runner, cli_path=Path("/opt/manage.sh"))
    report, ok = job.run("artifixer", source, '{"steps": 4}')
    assert ok is True
    assert "verdict: ok" in report
    assert "stdout: done" in report and "stderr: warning: slow" in report
    assert runner.calls[0][0] == [
        "/opt/manage.sh",
        "nvidia-lab",
        "run",
        "artifixer",
        "--input",
        source,
        "--params",
        '{"steps": 4}',
    ]
    assert runner.calls[0][1] == {
        "check": False,
        "capture_output": True,
        "text": True,
    }


def test_job_clips_long_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, monkeypatch, _doc(_tool()))
    runner = FakeRunner(stdout="x" * (nodes.OUTPUT_CLIP + 500), stderr="")
    report, ok = EZNvidiaLabJob(runner=runner).run("artifixer", _input_file(tmp_path), "")
    assert ok is True
    assert "..." in report
    assert len(report) > nodes.OUTPUT_CLIP


def test_job_reports_a_nonzero_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, _doc(_tool()))
    runner = FakeRunner(returncode=3, stdout="", stderr="boom")
    report, ok = EZNvidiaLabJob(runner=runner).run(
        "artifixer", _input_file(tmp_path), "{}"
    )
    assert ok is False
    assert "exited 3" in report and "stderr: boom" in report


def test_job_reports_a_cli_that_cannot_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, _doc(_tool()))
    runner = FakeRunner(error=OSError(2, "No such file or directory"))
    report, ok = EZNvidiaLabJob(runner=runner).run(
        "artifixer", _input_file(tmp_path), "{}"
    )
    assert ok is False
    assert "cannot start" in report and "No such file or directory" in report

    bare = FakeRunner(error=OSError())
    report, ok = EZNvidiaLabJob(runner=bare).run("artifixer", _input_file(tmp_path))
    assert ok is False and "cannot start" in report


def test_job_uses_subprocess_when_no_runner_is_injected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, _doc(_tool()))
    seen: list[list[str]] = []

    def _run(argv: list[str], **_kwargs: bool) -> FakeProc:
        seen.append(argv)
        return FakeProc(0, "ok", "")

    monkeypatch.setattr(nodes, "subprocess", SimpleNamespace(run=_run))
    report, ok = EZNvidiaLabJob().run("artifixer", _input_file(tmp_path))
    assert ok is True
    assert seen[0][1:] == [
        "nvidia-lab",
        "run",
        "artifixer",
        "--input",
        _input_file(tmp_path),
        "--params",
        "{}",
    ]
    assert "verdict: ok" in report


def test_default_runner_forwards_the_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _run(argv: list[str], **kwargs: bool) -> FakeProc:
        captured["argv"] = argv
        captured.update(kwargs)
        return FakeProc(0, "", "")

    monkeypatch.setattr(nodes, "subprocess", SimpleNamespace(run=_run))
    proc = nodes._default_runner(["true"], check=False, capture_output=True, text=True)
    assert proc.returncode == 0
    assert captured["argv"] == ["true"]
    assert captured["check"] is False
    assert captured["capture_output"] is True
    assert captured["text"] is True


def test_job_refuses_everything_before_running(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "not-here.zip"
    runner = FakeRunner()
    job = EZNvidiaLabJob(runner=runner)

    _write(tmp_path, monkeypatch, "{oops")
    report, ok = job.run("artifixer", "in", "{}")
    assert ok is False and "malformed JSON" in report

    _write(tmp_path, monkeypatch, _doc(_tool()))
    report, ok = job.run("", "in", "{}")
    assert ok is False and "widget tool_id is empty" in report

    report, ok = job.run("ghost", "in", "{}")
    assert ok is False and "no catalog row with id 'ghost'" in report

    _write(tmp_path, monkeypatch, _doc(_tool(status="blocked-license")))
    report, ok = job.run("artifixer", "in", "{}")
    assert ok is False and "refuses to run a row that is not opt-in" in report
    assert "status blocked-license" in report

    _write(tmp_path, monkeypatch, _doc(_tool()))
    report, ok = job.run("artifixer", "   ", "{}")
    assert ok is False and "widget input_path is empty" in report

    report, ok = job.run("artifixer", str(missing), "{}")
    assert ok is False and "is not a readable file" in report

    report, ok = job.run("artifixer", _input_file(tmp_path), "{nope")
    assert ok is False and "params_json is not valid JSON" in report

    assert runner.calls == []


def test_job_input_types() -> None:
    spec = EZNvidiaLabJob.INPUT_TYPES()
    assert spec["required"]["params_json"][1]["multiline"] is True
    assert spec["required"]["tool_id"][1]["default"] == "artifixer"


# --------------------------------------------------------------------------- #
# Verdict node
# --------------------------------------------------------------------------- #


def test_verdict_names_the_block_and_the_reopen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(
        tmp_path,
        monkeypatch,
        _doc(
            _tool(
                status="blocked-license",
                gate_notes="the license wall",
                reopen="when NVIDIA relicenses",
            ),
            _tool(id="artifixer-two", gate_notes="nothing", reopen="n/a"),
        ),
    )
    node = EZNvidiaLabVerdict()
    blocked = node.run("artifixer")["result"][0]
    assert "(blocked-license)" in blocked
    assert "reason: the license wall" in blocked
    assert "reopen: when NVIDIA relicenses" in blocked
    assert "verify: bazelisk test" in blocked

    opt_in = node.run(" artifixer-two ")["result"][0]
    assert "nothing blocks this row" in opt_in


def test_verdict_degrades(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    node = EZNvidiaLabVerdict()
    _write(tmp_path, monkeypatch, "{oops")
    assert "malformed JSON" in node.run("artifixer")["result"][0]
    _write(tmp_path, monkeypatch, _doc())
    assert "widget tool_id is empty" in node.run("")["result"][0]
    assert "no catalog row with id 'ghost'" in node.run("ghost")["result"][0]


def test_verdict_input_types() -> None:
    spec = EZNvidiaLabVerdict.INPUT_TYPES()
    assert spec["required"]["tool_id"][1]["default"] == "nurec-ga"


# --------------------------------------------------------------------------- #
# Fail-soft helpers: ez_common may be unimportable, so nothing may raise
# --------------------------------------------------------------------------- #


def test_log_and_path_helper_survive_a_missing_ez_common(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    custom = str(CUSTOM)
    _block_ez_common(monkeypatch)
    monkeypatch.setattr(sys, "path", [entry for entry in sys.path if entry != custom])

    nodes._log("hello")
    assert "[ez_nvidia_lab] hello" in capsys.readouterr().err
    assert custom in sys.path

    nodes._ensure_custom_nodes_path()
    assert capsys.readouterr().err == ""


def test_catalog_error_is_a_value_error() -> None:
    assert issubclass(CatalogError, ValueError)
    with pytest.raises(ValueError, match="schema"):
        parse_catalog(json.dumps({**_doc(), "schema": 9}))


def test_clip_keeps_short_text_whole() -> None:
    assert nodes._clip("short") == "short"
    assert nodes._shorten("short") == "short"
    assert nodes._shorten("x" * 80) == "x" * nodes.LICENSE_CLIP + "..."
