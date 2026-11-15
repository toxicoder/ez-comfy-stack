"""Tests for scripts/lib/nvidia_lab.py: the fail-closed tier catalog reader.

Hermetic: reads the committed catalog plus tmp_path fixtures; no network,
Docker, or GPU.
"""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import nvidia_lab  # noqa: E402

if TYPE_CHECKING:
    from ez_common import Json, JsonObject

REAL_CATALOG = ROOT / nvidia_lab.CATALOG_RELPATH

STATUS_VALUES = ["opt-in", "blocked-license", "blocked-platform", "deferred"]
COMMERCIAL_VALUES = ["permitted", "conditional", "non-commercial", "unknown", "none"]
ARM64_VALUES = ["published", "partial", "absent", "unknown", "na"]
ARTIFACT_VALUES = [
    "custom-nodes",
    "source-build",
    "container-image",
    "host-cli",
    "viewer",
    "paper-only",
]
COMFY_SHAPE_VALUES = ["node-pack", "host-cli", "sidecar", "viewer", "none"]


def weight(**changes: Json) -> JsonObject:
    """One valid weight row, with the given keys overridden.

    Args:
        **changes: Keys to overwrite on the row.

    Returns:
        A weight object the reader accepts.
    """
    row: JsonObject = {
        "source": "huggingface",
        "repo": "nvidia/alpha",
        "file": "alpha.pt",
        "gb": 6.4,
        "gated": False,
    }
    row.update(changes)
    return row


def app_block(**changes: Json) -> JsonObject:
    """One valid App block, with the given keys overridden.

    Args:
        **changes: Keys to overwrite on the block.

    Returns:
        An App object the reader accepts.
    """
    row: JsonObject = {
        "mode": "splat-train",
        "occupancy": "none",
        "deliverable": "a trained scene",
    }
    row.update(changes)
    return row


def tool(tool_id: str = "alpha", /, **changes: Json) -> JsonObject:
    """One valid tool row, with the given keys overridden.

    Args:
        tool_id: Id and graph tail for the row.
        **changes: Keys to overwrite on the row.

    Returns:
        A tool object the reader accepts.
    """
    row: JsonObject = {
        "id": tool_id,
        "title": "Alpha",
        "status": "opt-in",
        "task": "Trains a scene from a capture.",
        "input": "a capture",
        "output": "a Gaussian scene",
        "upstream": "https://github.com/nvidia/alpha",
        "see_also": ["https://example.com/alpha-paper"],
        "code_license": "Apache-2.0",
        "weights_license": "NVIDIA Research License",
        "commercial_use": "conditional",
        "weights": [weight(), weight(file="alpha-2.pt", gb=0, gated=True)],
        "artifact": "source-build",
        "artifact_ref": "https://github.com/nvidia/alpha.git",
        "arm64": "partial",
        "gb10": "unverified",
        "install": "git-clone",
        "cmd": "git clone https://github.com/nvidia/alpha",
        "vram_gb": 24,
        "disk_gb": 40,
        "comfy_shape": "host-cli",
        "nodes": ["EZNvidiaLabPreflight", "EZNvidiaLabJob"],
        "graph": f"labs/nvidia/{tool_id}",
        "app": app_block(),
        "gate_notes": "",
        "reopen": "Re-test when the weight license is stated.",
        "verify": "bazelisk test //tests:bats_nvidia_lab_test",
        "sources": ["https://github.com/nvidia/alpha"],
    }
    row.update(changes)
    return row


def catalog_doc(*tools: JsonObject, **changes: Json) -> JsonObject:
    """A whole schema-1 document holding the given tool rows.

    Args:
        *tools: Tool rows, kept in the order given.
        **changes: Top-level keys to overwrite.

    Returns:
        A catalog document carrying every declared enum list.
    """
    doc: JsonObject = {
        "schema": 1,
        "tier": "nvidia-lab",
        "tier_title": "NVIDIA lab",
        "updated": "2026-11-15",
        "status_values": list(STATUS_VALUES),
        "commercial_values": list(COMMERCIAL_VALUES),
        "arm64_values": list(ARM64_VALUES),
        "artifact_values": list(ARTIFACT_VALUES),
        "comfy_shape_values": list(COMFY_SHAPE_VALUES),
        "tools": list(tools),
    }
    doc.update(changes)
    return doc


def write_catalog(tmp_path: Path, doc: JsonObject) -> Path:
    """Serialize a catalog document into tmp_path.

    Args:
        tmp_path: pytest temporary directory.
        doc: Document to write.

    Returns:
        The path that was written.
    """
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def parse(tmp_path: Path, doc: JsonObject) -> nvidia_lab.Catalog:
    """Write a fixture document and read it back.

    Args:
        tmp_path: pytest temporary directory.
        doc: Document to hand the reader.

    Returns:
        The parsed catalog.
    """
    return nvidia_lab.load_catalog(write_catalog(tmp_path, doc))


def two_tool_doc() -> JsonObject:
    """A fixture catalog whose file order is not its id order.

    Returns:
        Document with a deferred ``beta`` row before an opt-in ``alpha`` row.
    """
    return catalog_doc(tool("beta", status="deferred", title="Beta"), tool("alpha"))


def expect_catalog_error(tmp_path: Path, doc: JsonObject, needle: str) -> None:
    """Assert the reader refuses a document, naming the offending location.

    Args:
        tmp_path: pytest temporary directory.
        doc: Document that must be refused.
        needle: Regex the CatalogError message must contain.
    """
    with pytest.raises(nvidia_lab.CatalogError, match=needle):
        nvidia_lab.load_catalog(write_catalog(tmp_path, doc))


def test_catalog_path_defaults_to_the_repo_catalog() -> None:
    assert nvidia_lab.catalog_path() == REAL_CATALOG
    assert nvidia_lab.catalog_path(env={}) == REAL_CATALOG
    assert nvidia_lab.catalog_path(env={nvidia_lab.CATALOG_ENV: ""}) == REAL_CATALOG
    assert nvidia_lab.catalog_path(env={nvidia_lab.CATALOG_ENV: "   "}) == REAL_CATALOG


def test_catalog_path_honours_the_env_override(tmp_path: Path) -> None:
    override = tmp_path / "fixture.json"
    assert nvidia_lab.catalog_path(env={nvidia_lab.CATALOG_ENV: f" {override} "}) == override


def test_real_catalog_loads_and_validates() -> None:
    parsed = nvidia_lab.load_catalog(REAL_CATALOG)
    assert parsed.schema == nvidia_lab.CATALOG_SCHEMA
    assert parsed.tier == "nvidia-lab"
    assert parsed.tier_title == "NVIDIA lab"
    assert len(parsed.updated) == len("2026-11-15")
    assert parsed.tools, "the shipped catalog must not be empty"
    ids = [row.id for row in parsed.tools]
    assert len(ids) == len(set(ids))
    for row in parsed.tools:
        assert row.graph == f"{nvidia_lab.GRAPH_PREFIX}{row.id}"
        assert row.app.occupancy == "none"
        assert row.status in STATUS_VALUES
        assert row.commercial_use in COMMERCIAL_VALUES
        assert row.arm64 in ARM64_VALUES
        assert row.artifact in ARTIFACT_VALUES
        assert row.comfy_shape in COMFY_SHAPE_VALUES
        assert row.gb10 in nvidia_lab.GB10_VALUES
        assert row.install in nvidia_lab.INSTALL_VALUES
        assert row.vram_gb >= 0 and row.disk_gb >= 0
        assert row.nodes and row.sources
        for item in row.weights:
            assert item.gb >= 0.0
            assert item.file and item.repo and item.source
    assert nvidia_lab.status_counts(parsed)
    assert all(row.status == "opt-in" for row in nvidia_lab.opt_in(parsed))


def test_json_verb_output_matches_the_file() -> None:
    parsed = nvidia_lab.load_catalog(REAL_CATALOG)
    row = next(item for item in parsed.tools if item.weights)
    raw: JsonObject = json.loads(REAL_CATALOG.read_text(encoding="utf-8"))
    rows = raw["tools"]
    assert isinstance(rows, list)
    source = next(item for item in rows if isinstance(item, dict) and item["id"] == row.id)
    assert nvidia_lab._tool_row(row) == source  # noqa: SLF001


def test_tool_by_id_hits_and_misses(tmp_path: Path) -> None:
    parsed = parse(tmp_path, two_tool_doc())
    assert nvidia_lab.tool_by_id(parsed, "alpha").title == "Alpha"
    with pytest.raises(nvidia_lab.CatalogError, match="unknown tool id"):
        nvidia_lab.tool_by_id(parsed, "nope")


def test_opt_in_and_status_counts(tmp_path: Path) -> None:
    parsed = parse(tmp_path, two_tool_doc())
    assert [row.id for row in nvidia_lab.opt_in(parsed)] == ["alpha"]
    counts = nvidia_lab.status_counts(parsed)
    assert counts == {"deferred": 1, "opt-in": 1}
    assert sum(counts.values()) == len(parsed.tools)


def test_weight_and_app_records(tmp_path: Path) -> None:
    alpha = nvidia_lab.tool_by_id(parse(tmp_path, two_tool_doc()), "alpha")
    assert alpha.weights[0].label() == "nvidia/alpha/alpha.pt@6.4"
    assert alpha.weights[1].label() == "nvidia/alpha/alpha-2.pt@0"
    assert alpha.app.label() == "splat-train|none|a trained scene"
    assert alpha.app.field("mode") == "splat-train"
    assert alpha.app.field("occupancy") == "none"
    assert alpha.app.field("deliverable") == "a trained scene"
    assert alpha.app.field("bogus") is None


def test_load_rejects_bad_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(nvidia_lab.CatalogError, match="invalid JSON"):
        nvidia_lab.load_catalog(path)


def test_load_rejects_a_non_object_document(tmp_path: Path) -> None:
    path = tmp_path / "array.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(nvidia_lab.CatalogError, match="expected an object"):
        nvidia_lab.load_catalog(path)


def test_load_rejects_unknown_top_level_key(tmp_path: Path) -> None:
    doc = catalog_doc(tool())
    doc["extra"] = "surprise"
    expect_catalog_error(tmp_path, doc, "unknown key extra")


@pytest.mark.parametrize("key", sorted(nvidia_lab.TOP_REQUIRED_KEYS))
def test_load_rejects_missing_top_level_key(tmp_path: Path, key: str) -> None:
    doc = catalog_doc(tool())
    del doc[key]
    expect_catalog_error(tmp_path, doc, f"missing key {key}")


def test_load_rejects_a_bad_schema(tmp_path: Path) -> None:
    expect_catalog_error(tmp_path, catalog_doc(tool(), schema=2), "expected 1, got 2")
    expect_catalog_error(tmp_path, catalog_doc(tool(), schema="1"), "expected an integer")


def test_load_rejects_a_non_string_enum_list(tmp_path: Path) -> None:
    doc = catalog_doc(tool())
    doc["status_values"] = ["opt-in", 7]
    expect_catalog_error(tmp_path, doc, r"status_values\[1\]")


def test_load_rejects_tools_that_are_not_an_array(tmp_path: Path) -> None:
    expect_catalog_error(tmp_path, catalog_doc(tool(), tools={}), "tools: expected an array")


def test_load_rejects_a_tool_that_is_not_an_object(tmp_path: Path) -> None:
    expect_catalog_error(
        tmp_path, catalog_doc(tool(), tools=["alpha"]), r"tools\[0\]: expected an object"
    )


def test_load_rejects_unknown_tool_key(tmp_path: Path) -> None:
    expect_catalog_error(tmp_path, catalog_doc(tool(nope="x")), "unknown key nope")


@pytest.mark.parametrize("key", list(nvidia_lab.TOOL_KEYS))
def test_load_rejects_missing_tool_key(tmp_path: Path, key: str) -> None:
    row = tool()
    del row[key]
    expect_catalog_error(tmp_path, catalog_doc(row), f"missing key {key}")


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("title", 5),
        ("see_also", "https://example.com"),
        ("nodes", ["EZNvidiaLabJob", 7]),
        ("vram_gb", "24"),
        ("disk_gb", True),
        ("graph", 3),
    ],
)
def test_load_rejects_wrong_field_types(tmp_path: Path, key: str, value: Json) -> None:
    expect_catalog_error(tmp_path, catalog_doc(tool(**{key: value})), key)


@pytest.mark.parametrize(
    "key",
    ["status", "commercial_use", "arm64", "artifact", "comfy_shape", "gb10", "install"],
)
def test_load_rejects_enum_tokens_outside_the_allowed_set(tmp_path: Path, key: str) -> None:
    expect_catalog_error(tmp_path, catalog_doc(tool(**{key: "not-a-token"})), key)


def test_load_rejects_a_non_string_enum(tmp_path: Path) -> None:
    expect_catalog_error(tmp_path, catalog_doc(tool(status=7)), "status: expected a string")


def test_load_rejects_an_unknown_occupancy(tmp_path: Path) -> None:
    expect_catalog_error(
        tmp_path, catalog_doc(tool(app=app_block(occupancy="klein-none"))), "occupancy"
    )


def test_load_rejects_an_empty_app_mode(tmp_path: Path) -> None:
    expect_catalog_error(tmp_path, catalog_doc(tool(app=app_block(mode=""))), "non-empty mode")


@pytest.mark.parametrize("key", ["mode", "occupancy", "deliverable"])
def test_load_rejects_missing_app_keys(tmp_path: Path, key: str) -> None:
    row = app_block()
    del row[key]
    expect_catalog_error(tmp_path, catalog_doc(tool(app=row)), f"app: missing key {key}")


def test_load_rejects_unknown_and_bad_app_keys(tmp_path: Path) -> None:
    expect_catalog_error(
        tmp_path, catalog_doc(tool(app=app_block(extra="x"))), "app: unknown key extra"
    )
    expect_catalog_error(
        tmp_path, catalog_doc(tool(app=app_block(deliverable=3))), "app.deliverable"
    )
    expect_catalog_error(
        tmp_path, catalog_doc(tool(app="splat-train")), r"tools\[0\].app: expected an object"
    )


@pytest.mark.parametrize("key", ["source", "repo", "file", "gb", "gated"])
def test_load_rejects_missing_weight_keys(tmp_path: Path, key: str) -> None:
    row = weight()
    del row[key]
    expect_catalog_error(tmp_path, catalog_doc(tool(weights=[row])), r"weights\[0\]: missing key")


def test_load_rejects_bad_weight_rows(tmp_path: Path) -> None:
    expect_catalog_error(
        tmp_path, catalog_doc(tool(weights=["alpha.pt"])), r"weights\[0\]: expected an object"
    )
    expect_catalog_error(
        tmp_path,
        catalog_doc(tool(weights=[weight(extra="x")])),
        r"weights\[0\]: unknown key extra",
    )
    expect_catalog_error(tmp_path, catalog_doc(tool(weights=[weight(gb=-1)])), "0 or more")
    expect_catalog_error(tmp_path, catalog_doc(tool(weights=[weight(gb="big")])), r"weights\[0\].gb")
    expect_catalog_error(tmp_path, catalog_doc(tool(weights=[weight(gb=True)])), r"weights\[0\].gb")
    expect_catalog_error(tmp_path, catalog_doc(tool(weights=[weight(source=1)])), r"weights\[0\].source")
    expect_catalog_error(tmp_path, catalog_doc(tool(weights="none")), "weights: expected an array")


@pytest.mark.parametrize("value", ["yes", "false", 0, 1, [], {}])
def test_load_rejects_a_gated_that_is_not_a_flag(tmp_path: Path, value: Json) -> None:
    """Only true, false, and null are gating states; anything else is refused."""
    expect_catalog_error(
        tmp_path,
        catalog_doc(tool(weights=[weight(gated=value)])),
        r"weights\[0\].gated: expected a boolean",
    )


def test_load_accepts_null_as_unchecked_gating(tmp_path: Path) -> None:
    """A null gated is a state of its own, not a false the row asserts."""
    alpha = nvidia_lab.tool_by_id(
        parse(tmp_path, catalog_doc(tool(weights=[weight(gated=None)]))), "alpha"
    )
    assert alpha.weights[0].gated is None


def test_json_verb_keeps_the_null_gating(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """``json`` hands back the null, so a shell verb cannot invent a false."""
    path = write_catalog(tmp_path, catalog_doc(tool(weights=[weight(gated=None)])))
    assert nvidia_lab.main(["--catalog", str(path), "json", "alpha"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["weights"][0]["gated"] is None


def test_real_catalog_keeps_the_measured_gating_cells() -> None:
    """Every shipped weight carries the HF flag it was read against.

    The cosmos size and flag are the HF-measured cells the page prints: the row
    once claimed 15 GB ungated against a 28.95 GB ``gated: "auto"`` repo. The
    reader still accepts ``null`` for a row nobody has checked, but the shipped
    catalog holds no such row, so an unchecked cell here means a regression.
    """
    parsed = nvidia_lab.load_catalog(REAL_CATALOG)
    rows = [item for row in parsed.tools for item in row.weights]
    assert rows, "the shipped catalog carries weights to check"
    unchecked = [item for item in rows if item.gated is None]
    assert not unchecked, f"unverified gating shipped: {[w.repo for w in unchecked]}"
    cosmos = nvidia_lab.tool_by_id(parsed, "cosmos-drive-dreams").weights[0]
    assert (cosmos.repo, cosmos.file, cosmos.gb, cosmos.gated) == (
        "nvidia/Cosmos-Transfer1-7B-Sample-AV",
        "base_model.pt",
        28.95,
        True,
    )


def test_load_rejects_a_graph_that_names_another_id(tmp_path: Path) -> None:
    expect_catalog_error(
        tmp_path, catalog_doc(tool(graph="labs/nvidia/omega")), "expected labs/nvidia/alpha"
    )


def test_load_rejects_a_duplicate_id(tmp_path: Path) -> None:
    expect_catalog_error(tmp_path, catalog_doc(tool("alpha"), tool("alpha")), "duplicate id alpha")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("text", "text"),
        (True, "true"),
        (False, "false"),
        (24, "24"),
        (6.4, "6.4"),
        (2.0, "2"),
        (["a", "b"], "a,b"),
        ({"mode": "x", "occupancy": "none"}, "x|none"),
        (None, ""),
    ],
)
def test_render_value(value: Json, expected: str) -> None:
    assert nvidia_lab._render_value(value) == expected  # noqa: SLF001


def test_cli_list_and_ids_are_sorted(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = write_catalog(tmp_path, two_tool_doc())
    assert nvidia_lab.main(["--catalog", str(path), "list"]) == 0
    assert capsys.readouterr().out == "alpha\topt-in\tAlpha\nbeta\tdeferred\tBeta\n"
    assert nvidia_lab.main(["--catalog", str(path), "ids"]) == 0
    assert capsys.readouterr().out == "alpha\nbeta\n"


def test_cli_status_and_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = write_catalog(tmp_path, two_tool_doc())
    assert nvidia_lab.main(["--catalog", str(path), "status", "beta"]) == 0
    assert capsys.readouterr().out == "deferred\n"
    assert nvidia_lab.main(["--catalog", str(path), "json", "alpha"]) == 0
    line = capsys.readouterr().out
    assert line.endswith("\n") and line.count("\n") == 1
    payload = json.loads(line)
    assert payload["id"] == "alpha"
    assert payload["app"] == {
        "mode": "splat-train",
        "occupancy": "none",
        "deliverable": "a trained scene",
    }
    assert payload["weights"][0] == {
        "source": "huggingface",
        "repo": "nvidia/alpha",
        "file": "alpha.pt",
        "gb": 6.4,
        "gated": False,
    }


def test_cli_fields_renders_every_shape(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = write_catalog(tmp_path, two_tool_doc())
    keys = "id,status,weights,app,app.occupancy,vram_gb,see_also,nodes"
    assert nvidia_lab.main(["--catalog", str(path), "fields", "alpha", keys]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "id=alpha",
        "status=opt-in",
        "weights=nvidia/alpha/alpha.pt@6.4,nvidia/alpha/alpha-2.pt@0",
        "app=splat-train|none|a trained scene",
        "app.occupancy=none",
        "vram_gb=24",
        "see_also=https://example.com/alpha-paper",
        "nodes=EZNvidiaLabPreflight,EZNvidiaLabJob",
    ]


def test_cli_fields_rejects_an_unknown_key(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_catalog(tmp_path, two_tool_doc())
    assert nvidia_lab.main(["--catalog", str(path), "fields", "alpha", "title,bogus"]) == 2
    assert "unknown field 'bogus'" in capsys.readouterr().err
    assert nvidia_lab.main(["--catalog", str(path), "fields", "alpha", "app.bogus"]) == 2
    assert "unknown field 'app.bogus'" in capsys.readouterr().err


def test_cli_fields_needs_a_key_list(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_catalog(tmp_path, two_tool_doc())
    assert nvidia_lab.main(["--catalog", str(path), "fields", "alpha"]) == 2
    assert "needs a comma-separated key list" in capsys.readouterr().err


def test_cli_check_reports_the_tool_count(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_catalog(tmp_path, two_tool_doc())
    assert nvidia_lab.main(["--catalog", str(path), "check"]) == 0
    assert capsys.readouterr().out == "ok 2 tools\n"


def test_cli_check_reports_the_reason_and_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_catalog(tmp_path, catalog_doc(tool(), schema=9))
    assert nvidia_lab.main(["--catalog", str(path), "check"]) == 1
    err = capsys.readouterr().err
    assert err.startswith(f"{nvidia_lab.BIN}: {path}: ")
    assert "schema" in err


def test_cli_missing_catalog_exits_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "absent.json"
    assert nvidia_lab.main(["--catalog", str(missing), "list"]) == 1
    assert "No such file or directory" in capsys.readouterr().err


def test_cli_uses_the_env_override(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_catalog(tmp_path, two_tool_doc())
    monkeypatch.setenv(nvidia_lab.CATALOG_ENV, str(path))
    assert nvidia_lab.main(["ids"]) == 0
    assert capsys.readouterr().out == "alpha\nbeta\n"
    monkeypatch.setenv(nvidia_lab.CATALOG_ENV, str(tmp_path / "gone.json"))
    assert nvidia_lab.main(["check"]) == 1
    assert "gone.json" in capsys.readouterr().err


def test_cli_rejects_an_unknown_verb(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_catalog(tmp_path, two_tool_doc())
    assert nvidia_lab.main(["--catalog", str(path), "nope"]) == 2
    assert "unknown verb 'nope'" in capsys.readouterr().err


def test_cli_rejects_no_verb(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = write_catalog(tmp_path, two_tool_doc())
    assert nvidia_lab.main(["--catalog", str(path)]) == 2
    assert nvidia_lab.USAGE in capsys.readouterr().err


def test_cli_rejects_a_catalog_flag_without_a_value(capsys: pytest.CaptureFixture[str]) -> None:
    assert nvidia_lab.main(["--catalog"]) == 2
    assert "--catalog needs a path" in capsys.readouterr().err


def test_cli_rejects_a_missing_or_unknown_id(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_catalog(tmp_path, two_tool_doc())
    assert nvidia_lab.main(["--catalog", str(path), "status"]) == 2
    assert "status needs a tool id" in capsys.readouterr().err
    assert nvidia_lab.main(["--catalog", str(path), "json", "nope"]) == 2
    assert "unknown tool id" in capsys.readouterr().err


def test_cli_help_prints_usage(capsys: pytest.CaptureFixture[str]) -> None:
    assert nvidia_lab.main(["--help"]) == 0
    assert capsys.readouterr().out == f"{nvidia_lab.USAGE}\n"


def test_module_main_guard(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["nvidia_lab.py", "--help"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(ROOT / "scripts" / "lib" / "nvidia_lab.py"), run_name="__main__")
    assert exc.value.code == 0
    assert capsys.readouterr().out == f"{nvidia_lab.USAGE}\n"
