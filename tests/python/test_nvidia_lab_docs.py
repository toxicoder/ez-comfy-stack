"""Hermetic tests for the NVIDIA lab tier docs generator and its two pages.

Covers ``docs/generate_nvidia_lab_docs.py`` (reader rule, deterministic render,
idempotent write), the generated reference page, and the authored
``docs/nvidia-lab.mdx`` page. Stdlib + the generator module; the catalog is the
repo's own ``custom_nodes/ez_nvidia_lab/catalog.json`` unless a test points
``EZ_NVIDIA_LAB_CATALOG`` at a fixture. Generated output goes to a tmp dir so no
test rewrites the committed page, except the entry-point smoke test, which
republishes identical bytes.
"""

from __future__ import annotations

import importlib.util
import json
import re
import runpy
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_TESTS_DIR = Path(__file__).resolve().parents[1]
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

import bazel_docs  # noqa: E402  (import after the sys.path insert above)

ROOT = _TESTS_DIR.parent
GEN_PY = ROOT / "docs" / "generate_nvidia_lab_docs.py"
CATALOG = ROOT / "custom_nodes" / "ez_nvidia_lab" / "catalog.json"
GENERATED = ROOT / "docs" / "generated" / "nvidia-lab" / "tier.md"
PAGE = ROOT / "docs" / "nvidia-lab.mdx"

# Swept by the repo's own Bazel-is-the-ingress guard, in command position.
SWEPT_PATHS = (
    "docs/generate_nvidia_lab_docs.py",
    "docs/nvidia-lab.mdx",
    "docs/generated/nvidia-lab/tier.md",
)

# Every catalog row the pages have to name.
EXPECTED_IDS = (
    "artifixer",
    "3dgrut",
    "3dgrut-artifixer-fork",
    "nurec-ga",
    "instant-nurec",
    "lyra-1",
    "lyra-2",
    "pixelumm",
    "gamma-world",
    "gen3c",
    "luxdit",
    "infinicube",
    "cosmos-drive-dreams",
    "dvlt",
    "dlss5-enhancer",
    "splatpainting",
    "vk-gaussian-splatting",
    "asset-harvester",
)

# Words that make a backticked span a command rather than a term.
_COMMAND_WORDS = frozenset(
    {
        "apt",
        "apt-get",
        "bash",
        "bazel",
        "bazelisk",
        "curl",
        "docker",
        "git",
        "hf",
        "huggingface-cli",
        "make",
        "npm",
        "npx",
        "pip",
        "pip3",
        "pytest",
        "python",
        "python3",
        "sh",
        "source",
        "sudo",
        "systemctl",
    }
)
# A repo script named where a reader would copy it.
_RAW_SCRIPT_RE = re.compile(r"\b(?:docker|docs|lints|scripts|tests|tools)/[\w./-]+\.(?:bash|bats|py|sh)\b")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_CODE_SPAN_RE = re.compile(r"(`+)(.+?)\1", re.S)
_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
_BARE_VARIABLE_RE = re.compile(r"^\$\{?[A-Za-z_][A-Za-z0-9_]*\}?$")
_ASSIGNMENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=\S+")


def _load_generator() -> ModuleType:
    """Load ``docs/generate_nvidia_lab_docs.py`` as a module.

    Returns:
        The generator module.
    """
    spec = importlib.util.spec_from_file_location("ez_generate_nvidia_lab_docs", GEN_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ez_generate_nvidia_lab_docs"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def gen() -> ModuleType:
    """The loaded generator module.

    Returns:
        The generator module.
    """
    return _load_generator()


def _weight(**overrides: object) -> dict[str, object]:
    """One complete weight entry.

    Args:
        **overrides: Keys to replace on the base entry.

    Returns:
        A weight payload.
    """
    base: dict[str, object] = {
        "source": "huggingface",
        "repo": "nvidia/Synthetic",
        "file": "small.pt",
        "gb": 1.5,
        "gated": True,
    }
    base.update(overrides)
    return base


def _tool_payload(tool_id: str = "synthetic", **overrides: object) -> dict[str, object]:
    """One complete tool entry, with every key the reader requires.

    Args:
        tool_id: Row id.
        **overrides: Keys to replace on the base entry.

    Returns:
        A tool payload.
    """
    base: dict[str, object] = {
        "id": tool_id,
        "title": "Synthetic",
        "status": "opt-in",
        "task": "Turns one image into one clip.",
        "input": "one image",
        "output": "one clip",
        "upstream": "https://example.invalid/synthetic",
        "see_also": ["https://example.invalid/synthetic/card"],
        "code_license": "Apache-2.0",
        "weights_license": "NVIDIA Open Model License",
        "commercial_use": "permitted",
        "weights": [_weight()],
        "artifact": "source-build",
        "artifact_ref": "https://example.invalid/synthetic.git",
        "arm64": "published",
        "gb10": "verified",
        "install": "git-clone",
        "cmd": "",
        "vram_gb": 24,
        "disk_gb": 20,
        "comfy_shape": "host-cli",
        "nodes": ["EZNvidiaLabPreflight"],
        "graph": "labs/nvidia/synthetic",
        "app": {"mode": "splat-train", "occupancy": "none", "deliverable": "one clip"},
        "gate_notes": "Synthetic row used only by tests.",
        "reopen": "n/a - this row is installable.",
        "verify": "bazelisk test //tests:bats_nvidia_lab_test",
        "sources": ["https://example.invalid/synthetic/src"],
    }
    base.update(overrides)
    return base


def _catalog_payload(tools: list[dict[str, object]]) -> dict[str, object]:
    """One complete catalog document.

    Args:
        tools: Tool payloads.

    Returns:
        A catalog payload whose status list holds one unused value.
    """
    return {
        "schema": 1,
        "tier": "nvidia-lab",
        "tier_title": "NVIDIA lab",
        "updated": "2026-11-15",
        "status_values": ["opt-in", "blocked-license", "blocked-platform", "deferred", "retired"],
        "commercial_values": ["permitted", "conditional", "non-commercial", "unknown", "none"],
        "arm64_values": ["published", "partial", "absent", "unknown", "na"],
        "artifact_values": [
            "custom-nodes",
            "source-build",
            "container-image",
            "host-cli",
            "viewer",
            "paper-only",
        ],
        "comfy_shape_values": ["node-pack", "host-cli", "sidecar", "viewer", "none"],
        "tools": tools,
    }


def _write_catalog(tmp_path: Path, payload: dict[str, object]) -> Path:
    """Write a catalog payload to a tmp file.

    Args:
        tmp_path: Pytest tmp directory.
        payload: The document to write.

    Returns:
        The path of the written catalog.
    """
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _tool_of(payload: dict[str, object]) -> dict[str, object]:
    """Return the first tool entry of a catalog payload.

    Args:
        payload: A catalog payload.

    Returns:
        The first tool entry.
    """
    tools = payload["tools"]
    assert isinstance(tools, list)
    first = tools[0]
    assert isinstance(first, dict)
    return first


def _weight_of(payload: dict[str, object]) -> dict[str, object]:
    """Return the first weight entry of the first tool of a payload.

    Args:
        payload: A catalog payload.

    Returns:
        The first weight entry.
    """
    weights = _tool_of(payload)["weights"]
    assert isinstance(weights, list)
    first = weights[0]
    assert isinstance(first, dict)
    return first


def _app_of(payload: dict[str, object]) -> dict[str, object]:
    """Return the app block of the first tool of a payload.

    Args:
        payload: A catalog payload.

    Returns:
        The app block.
    """
    app = _tool_of(payload)["app"]
    assert isinstance(app, dict)
    return app


def _set(target: dict[str, object], key: str, value: object) -> None:
    """Set one key of a catalog node.

    Args:
        target: The node to change.
        key: Key to write.
        value: New value.

    Returns:
        None.
    """
    target[key] = value


def _drop(target: dict[str, object], key: str) -> None:
    """Delete one key of a catalog node.

    Args:
        target: The node to change.
        key: Key to delete.

    Returns:
        None.
    """
    del target[key]


_BAD_CASES: tuple[tuple[str, Callable[[dict[str, object]], None], str], ...] = (
    ("schema not one", lambda c: _set(c, "schema", 2), "expected 1"),
    ("schema not an integer", lambda c: _set(c, "schema", "1"), "expected an integer"),
    ("schema a boolean", lambda c: _set(c, "schema", True), "expected an integer"),
    ("tier renamed", lambda c: _set(c, "tier", "other-lab"), "expected nvidia-lab"),
    ("tier not a string", lambda c: _set(c, "tier", 7), "expected a string"),
    ("top level key missing", lambda c: _drop(c, "tier_title"), "missing key tier_title"),
    ("top level key unknown", lambda c: _set(c, "publisher", "nvidia"), "unknown key publisher"),
    ("updated not a string", lambda c: _set(c, "updated", 20261115), "expected a string"),
    ("status list not an array", lambda c: _set(c, "status_values", "opt-in"), "expected a JSON array"),
    ("status list not strings", lambda c: _set(c, "status_values", [1]), "array of strings"),
    ("tools not an array", lambda c: _set(c, "tools", {}), "expected a JSON array"),
    ("tool not an object", lambda c: _set(c, "tools", [["id"]]), "expected a JSON object"),
    ("tool key missing", lambda c: _drop(_tool_of(c), "gate_notes"), "missing key gate_notes"),
    ("tool key unknown", lambda c: _set(_tool_of(c), "notes", "x"), "unknown key notes"),
    ("status outside the enum", lambda c: _set(_tool_of(c), "status", "maybe"), "outside the declared values"),
    ("artifact outside the enum", lambda c: _set(_tool_of(c), "artifact", "binary"), "outside the declared values"),
    ("commercial outside the enum", lambda c: _set(_tool_of(c), "commercial_use", "free"), "outside the declared values"),
    ("status not a string", lambda c: _set(_tool_of(c), "status", 3), "expected a string"),
    ("title not a string", lambda c: _set(_tool_of(c), "title", 3), "expected a string"),
    ("see_also not an array", lambda c: _set(_tool_of(c), "see_also", "url"), "expected a JSON array"),
    ("see_also not strings", lambda c: _set(_tool_of(c), "see_also", [1]), "array of strings"),
    ("nodes not strings", lambda c: _set(_tool_of(c), "nodes", [1]), "array of strings"),
    ("install not a string", lambda c: _set(_tool_of(c), "install", 1), "expected a string"),
    ("cmd not a string", lambda c: _set(_tool_of(c), "cmd", 1), "expected a string"),
    ("graph not a string", lambda c: _set(_tool_of(c), "graph", 1), "expected a string"),
    ("verify not a string", lambda c: _set(_tool_of(c), "verify", 1), "expected a string"),
    ("app mode not a string", lambda c: _set(_app_of(c), "mode", 1), "expected a string"),
    ("app occupancy not a string", lambda c: _set(_app_of(c), "occupancy", 1), "expected a string"),
    ("sources not an array", lambda c: _set(_tool_of(c), "sources", "url"), "expected a JSON array"),
    ("weights not an array", lambda c: _set(_tool_of(c), "weights", {}), "expected a JSON array"),
    ("weight not an object", lambda c: _set(_tool_of(c), "weights", ["x"]), "expected a JSON object"),
    ("weight key missing", lambda c: _drop(_weight_of(c), "gated"), "missing key gated"),
    ("weight key unknown", lambda c: _set(_weight_of(c), "sha256", "x"), "unknown key sha256"),
    ("weight gb not a number", lambda c: _set(_weight_of(c), "gb", "big"), "expected a number"),
    ("weight gb a boolean", lambda c: _set(_weight_of(c), "gb", True), "expected a number"),
    ("weight gated not a flag", lambda c: _set(_weight_of(c), "gated", "yes"), "expected a boolean"),
    ("vram not an integer", lambda c: _set(_tool_of(c), "vram_gb", "24"), "expected an integer"),
    ("vram a boolean", lambda c: _set(_tool_of(c), "vram_gb", True), "expected an integer"),
    ("disk not an integer", lambda c: _set(_tool_of(c), "disk_gb", 20.5), "expected an integer"),
    ("app not an object", lambda c: _set(_tool_of(c), "app", "none"), "expected a JSON object"),
    ("app key missing", lambda c: _drop(_app_of(c), "deliverable"), "missing key deliverable"),
    ("app key unknown", lambda c: _set(_app_of(c), "owner", "lab"), "unknown key owner"),
    (
        "duplicate tool id",
        lambda c: _set(c, "tools", [_tool_payload(), _tool_payload()]),
        "duplicate tool id",
    ),
)


def _fenced_and_spans(text: str) -> tuple[list[str], list[str]]:
    """Split a document into fenced lines and backticked spans.

    Args:
        text: Markdown or MDX text.

    Returns:
        ``(fenced_lines, code_spans)`` with the fence delimiters and fence info
        strings dropped.
    """
    fenced: list[str] = []
    spans: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        marker = _FENCE_RE.match(line)
        if marker is not None:
            if fence is None:
                fence = marker.group(1)
            elif marker.group(1) == fence:
                fence = None
            continue
        if fence is not None:
            if line.strip():
                fenced.append(line.strip())
            continue
        for match in _CODE_SPAN_RE.finditer(line):
            for part in match.group(2).splitlines():
                if part.strip():
                    spans.append(part.strip())
    return fenced, spans


def _looks_like_command(span: str) -> bool:
    """Decide whether a code span is a command a reader could paste.

    Args:
        span: One backticked span.

    Returns:
        True when the span names an executable, an assignment prefix, or a repo
        script path; False for a term such as ``gb10`` or a path with no
        executable in it.
    """
    if _RAW_SCRIPT_RE.search(span):
        return True
    if span.startswith(("./", "/", "~")):
        return True
    if span.startswith("$") and not _BARE_VARIABLE_RE.match(span):
        return True
    tokens = span.split()
    if not tokens:
        return False
    return tokens[0] in _COMMAND_WORDS or bool(_ASSIGNMENT_RE.fullmatch(tokens[0]))


def _frontmatter(text: str) -> dict[str, str]:
    """Parse the flat keys of a page's YAML frontmatter block.

    Args:
        text: Page text.

    Returns:
        Mapping of key to raw value; empty when there is no block.
    """
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        return {}
    keys: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            keys[key.strip()] = value.strip()
    return keys


def _table_row(text: str, tool_id: str) -> str:
    """Return the master-table line of one tool.

    Args:
        text: Page text.
        tool_id: Row id whose line is wanted.

    Returns:
        The one table line that carries that id in its first cell.

    Raises:
        AssertionError: The id is missing from the table or appears twice.
    """
    rows = [line for line in text.splitlines() if line.startswith(f"| {tool_id} | ")]
    assert len(rows) == 1, f"{tool_id}: expected one table row, found {len(rows)}"
    return rows[0]


def _table_cells(row: str) -> list[str]:
    """Split one master-table line into its stripped cells.

    Args:
        row: A line taken from :func:`_table_row`.

    Returns:
        One entry per column.
    """
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def _card_line(text: str, tool_id: str, label: str) -> str:
    """Return one labelled bullet from one tool card.

    Args:
        text: Page text.
        tool_id: Row id whose card is wanted.
        label: Bullet label, e.g. ``**Weights**``.

    Returns:
        The card line that starts with ``- <label>:``.

    Raises:
        AssertionError: The card or the labelled line is absent.
    """
    lines = text.splitlines()
    headers = [i for i, line in enumerate(lines) if line.startswith(f"### `{tool_id}` - ")]
    assert headers, f"{tool_id}: no tool card"
    prefix = f"- {label}:"
    for line in lines[headers[0] + 1 :]:
        if line.startswith("#"):
            break
        if line.startswith(prefix):
            return line
    raise AssertionError(f"{tool_id}: no {label} line in its card")


class TestReaderRule:
    """The catalog reader fails closed and names the offending key."""

    def test_reader_accepts_the_repo_catalog(self, gen: ModuleType) -> None:
        """The committed catalog validates and holds the eighteen rows."""
        catalog = gen.load_catalog(CATALOG)
        assert [tool.tool_id for tool in catalog.tools] == sorted(EXPECTED_IDS)
        assert catalog.tier_title == "NVIDIA lab"

    def test_reader_rejects_a_non_object_document(self, gen: ModuleType) -> None:
        """A list or a scalar where an object belongs is a reader error."""
        documents: list[Any] = [[], "nvidia-lab", 7, None]
        for payload in documents:
            with pytest.raises(ValueError, match="expected a JSON object"):
                gen.validate_catalog(payload)

    @pytest.mark.parametrize(("label", "mutation", "needle"), _BAD_CASES, ids=[c[0] for c in _BAD_CASES])
    def test_reader_rejects_a_malformed_catalog(
        self,
        gen: ModuleType,
        tmp_path: Path,
        label: str,
        mutation: Callable[[dict[str, object]], None],
        needle: str,
    ) -> None:
        """Each broken key or value raises ``ValueError`` naming the key."""
        del label
        payload = _catalog_payload([_tool_payload()])
        mutation(payload)
        path = _write_catalog(tmp_path, payload)
        with pytest.raises(ValueError, match=re.escape(needle)):
            gen.load_catalog(path)

    def test_reader_rejects_a_missing_catalog(self, gen: ModuleType, tmp_path: Path) -> None:
        """A catalog path that does not exist is a reader error."""
        with pytest.raises(ValueError, match="catalog not found"):
            gen.load_catalog(tmp_path / "absent.json")

    def test_reader_rejects_malformed_json(self, gen: ModuleType, tmp_path: Path) -> None:
        """A file that is not JSON fails the reader rather than the writer."""
        path = tmp_path / "catalog.json"
        path.write_text("{not json", encoding="utf-8")
        with pytest.raises(ValueError):
            gen.load_catalog(path)


class TestRenderer:
    """The render is deterministic and carries every catalog fact."""

    def test_render_sorts_rows_by_id(self, gen: ModuleType) -> None:
        """Rows appear in tool-id order regardless of catalog order."""
        payload = _catalog_payload([_tool_payload("zeta"), _tool_payload("alpha")])
        catalog = gen.validate_catalog(payload)
        text = gen.render_tier(catalog)
        assert text.index("### `alpha`") < text.index("### `zeta`")

    def test_render_is_deterministic(self, gen: ModuleType) -> None:
        """Two renders of the same catalog are byte-identical."""
        catalog = gen.validate_catalog(_catalog_payload([_tool_payload()]))
        assert gen.render_tier(catalog) == gen.render_tier(catalog)

    def test_render_ends_with_one_newline_and_no_cr(self, gen: ModuleType) -> None:
        """The page is LF-only and ends in exactly one trailing newline."""
        catalog = gen.validate_catalog(_catalog_payload([_tool_payload()]))
        text = gen.render_tier(catalog)
        assert "\r" not in text
        assert text.endswith("\n")
        assert not text.endswith("\n\n")

    def test_render_names_every_status_in_catalog_order(self, gen: ModuleType) -> None:
        """Every declared status gets a section, in the order the catalog lists."""
        catalog = gen.validate_catalog(_catalog_payload([_tool_payload()]))
        text = gen.render_tier(catalog)
        positions = [text.index(f"### {status}") for status in catalog.status_values]
        assert positions == sorted(positions)
        assert "- none" in text  # the status no row carries still gets a section

    def test_render_falls_back_for_empty_lists(self, gen: ModuleType) -> None:
        """A row with no see-also, no weights, and no artifact ref says none."""
        tool = _tool_payload("bare", see_also=[], weights=[], artifact_ref="")
        catalog = gen.validate_catalog(_catalog_payload([tool]))
        text = gen.render_tier(catalog)
        assert "- **See also**: none" in text
        assert "- **Weights**: none" in text
        assert "- **Artifact ref**: none" in text

    def test_render_escapes_table_pipes(self, gen: ModuleType) -> None:
        """A pipe in a license string cannot break the master table."""
        tool = _tool_payload("pipey", code_license="Apache-2.0 | MIT")
        catalog = gen.validate_catalog(_catalog_payload([tool]))
        text = gen.render_tier(catalog)
        assert "Apache-2.0 \\| MIT" in text

    def test_render_labels_every_card_field(self, gen: ModuleType) -> None:
        """Each card carries the task, I/O, links, weights, and verdict lines."""
        catalog = gen.validate_catalog(_catalog_payload([_tool_payload()]))
        text = gen.render_tier(catalog)
        for label in (
            "- **Task**:",
            "- **Input**:",
            "- **Output**:",
            "- **Upstream**:",
            "- **See also**:",
            "- **Weights**:",
            "- **Artifact ref**:",
            "- **Gate notes**:",
            "- **Reopen**:",
            "**Sources**",
        ):
            assert label in text
        assert "(1.5 GB, gated)" in text


class TestUnpublishedFigures:
    """A catalog 0 means no published figure, and the page says so."""

    def test_zero_figures_render_the_marker(self, gen: ModuleType) -> None:
        """A 0 footprint and a 0 weight print the marker, never a zero."""
        tool = _tool_payload("zeroed", vram_gb=0, disk_gb=0, weights=[_weight(gb=0)])
        text = gen.render_tier(gen.validate_catalog(_catalog_payload([tool])))
        cells = _table_cells(_table_row(text, "zeroed"))
        assert cells[-2:] == [gen.NOT_PUBLISHED, gen.NOT_PUBLISHED]
        assert "| 0 |" not in _table_row(text, "zeroed")
        weights = _card_line(text, "zeroed", "**Weights**")
        assert weights == (
            f"- **Weights**: `nvidia/Synthetic` / `small.pt` "
            f"({gen.NOT_PUBLISHED}, gated)"
        )
        assert "0 GB" not in weights

    def test_published_figures_still_print_their_numbers(self, gen: ModuleType) -> None:
        """The marker is only for 0; a real figure keeps its digits."""
        text = gen.render_tier(gen.validate_catalog(_catalog_payload([_tool_payload()])))
        assert _table_cells(_table_row(text, "synthetic"))[-2:] == ["24", "20"]
        assert "(1.5 GB, gated)" in _card_line(text, "synthetic", "**Weights**")

    def test_generated_page_marks_the_unpublished_footprints(
        self,
        gen: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The real page says so for the two rows whose footprint is 0."""
        del capsys
        monkeypatch.delenv(gen.CATALOG_ENV, raising=False)
        out = tmp_path / "tier.md"
        assert gen.main(["--out", str(out)]) == 0
        text = out.read_text(encoding="utf-8")
        for tool_id in ("gamma-world", "asset-harvester"):
            row = _table_row(text, tool_id)
            assert _table_cells(row)[-2:] == [gen.NOT_PUBLISHED, gen.NOT_PUBLISHED], row
            assert "| 0 |" not in row

    def test_the_node_pack_shares_the_wording(self, gen: ModuleType) -> None:
        """The pack's card view and this page tell the same sentence for a 0."""
        from ez_nvidia_lab import nodes  # noqa: PLC0415  (pack import, tests only)

        assert nodes.NOT_PUBLISHED == gen.NOT_PUBLISHED
        assert nodes.GATING_NOT_CHECKED == gen.GATING_NOT_CHECKED


class TestWeightShapes:
    """A weight file names a path, a tree, or a shard set, and the page says which.

    Every value here is the cell HF reports for that repo; the page used to
    print all three shapes as one backticked path.
    """

    def test_a_single_file_keeps_the_bare_path(self, gen: ModuleType) -> None:
        """No star and no trailing slash means one file, as before."""
        tool = _tool_payload("onedot", weights=[_weight(file="base_model.pt", gb=28.95, gated=True)])
        text = gen.render_tier(gen.validate_catalog(_catalog_payload([tool])))
        assert _card_line(text, "onedot", "**Weights**") == (
            "- **Weights**: `nvidia/Synthetic` / `base_model.pt` (28.95 GB, gated)"
        )

    def test_a_directory_and_a_shard_set_say_which(self, gen: ModuleType) -> None:
        """A trailing slash is a tree and a star is a shard set, not a file."""
        tool = _tool_payload(
            "many",
            weights=[
                _weight(file="checkpoints/"),
                _weight(file="S8-F*-R*/*.distcp", gb=121.6),
            ],
        )
        text = gen.render_tier(gen.validate_catalog(_catalog_payload([tool])))
        assert _card_line(text, "many", "**Weights**") == (
            "- **Weights**: `nvidia/Synthetic` / tree: `checkpoints/` (1.5 GB, gated); "
            "`nvidia/Synthetic` / shards: `S8-F*-R*/*.distcp` (121.6 GB, gated)"
        )

    def test_null_is_a_valid_gating_state(self, gen: ModuleType) -> None:
        """The reader keeps null as itself instead of coercing it to false."""
        tool = _tool_payload("unchecked2", weights=[_weight(gated=None)])
        catalog = gen.validate_catalog(_catalog_payload([tool]))
        assert catalog.tools[0].weights[0].gated is None

    def test_an_unchecked_flag_is_not_printed_as_ungated(self, gen: ModuleType) -> None:
        """Null gating renders the marker, never the open-repo claim."""
        tool = _tool_payload("unchecked", weights=[_weight(gated=None)])
        text = gen.render_tier(gen.validate_catalog(_catalog_payload([tool])))
        line = _card_line(text, "unchecked", "**Weights**")
        assert line == (
            "- **Weights**: `nvidia/Synthetic` / `small.pt` "
            f"(1.5 GB, {gen.GATING_NOT_CHECKED})"
        )
        assert "ungated" not in line

    def test_the_shipped_rows_print_the_measured_cells(self, gen: ModuleType) -> None:
        """The rows HF was read against carry its size, path, and gating."""
        catalog = gen.load_catalog(gen.DEFAULT_CATALOG_PATH)
        page = gen.render_tier(catalog)
        expected = {
            "cosmos-drive-dreams": (
                "`nvidia/Cosmos-Transfer1-7B-Sample-AV` / `base_model.pt` "
                "(28.95 GB, gated)"
            ),
            "infinicube": (
                "`yifanlu/InfiniCube-checkpoints` / tree: `checkpoints/` "
                "(82.3 GB, ungated)"
            ),
            "dvlt": "`nvidia/dvlt` / `model.safetensors` (0.47 GB, ungated)",
        }
        for tool_id, cells in expected.items():
            assert _card_line(page, tool_id, "**Weights**") == f"- **Weights**: {cells}"


class TestGeneratedPage:
    """The committed generated page is current, complete, and clean."""

    def test_committed_page_matches_the_generator(self, gen: ModuleType) -> None:
        """The committed page is exactly what the generator writes today."""
        assert GENERATED.is_file(), "commit docs/generated/nvidia-lab/tier.md"
        assert GENERATED.read_text(encoding="utf-8") == gen.render_tier(gen.load_catalog(CATALOG))

    def test_generated_page_names_every_catalog_id(self) -> None:
        """Every catalog id is readable on the generated page."""
        text = GENERATED.read_text(encoding="utf-8")
        missing = [tool_id for tool_id in EXPECTED_IDS if f"`{tool_id}`" not in text]
        assert missing == []

    def test_generated_table_has_one_row_per_tool(self) -> None:
        """The master table carries exactly one row per catalog tool."""
        text = GENERATED.read_text(encoding="utf-8")
        rows = [
            line
            for line in text.splitlines()
            if line.startswith("| ") and not line.startswith("| ---") and not line.startswith("| id ")
        ]
        assert len(rows) == len(EXPECTED_IDS)


class TestAuthoredPage:
    """The operator page names every row and keeps the house chrome."""

    def test_page_names_every_catalog_id(self) -> None:
        """All eighteen rows appear on the authored page."""
        text = PAGE.read_text(encoding="utf-8")
        missing = [tool_id for tool_id in EXPECTED_IDS if f"`{tool_id}`" not in text]
        assert missing == []

    def test_page_frontmatter_has_the_house_keys(self) -> None:
        """Frontmatter carries title, description, and tags."""
        keys = _frontmatter(PAGE.read_text(encoding="utf-8"))
        for key in ("title", "description", "tags"):
            assert keys.get(key), f"frontmatter missing {key}"

    def test_generated_page_frontmatter_has_the_house_keys(self) -> None:
        """The generated reference carries title, description, and tags."""
        keys = _frontmatter(GENERATED.read_text(encoding="utf-8"))
        for key in ("title", "description", "tags"):
            assert keys.get(key), f"frontmatter missing {key}"

    def test_page_links_the_generated_reference(self) -> None:
        """The page points at the generated reference by relative path."""
        text = PAGE.read_text(encoding="utf-8")
        assert "generated/nvidia-lab/tier.md" in text

    def test_page_states_the_gates_and_the_occupancy_rule(self) -> None:
        """The four gates, the no-download rule, and the XOR stay on the page."""
        text = PAGE.read_text(encoding="utf-8")
        for needle in (
            "linux_aarch64",
            "One heavy GPU job",
            "adds no Compose service",
            "nvidia-lab status",
            "unless its row says `verified`",
        ):
            assert needle in text


class TestCommandPositions:
    """No command a reader copies may name a raw script."""

    def test_every_fenced_command_is_the_bazel_form(self) -> None:
        """Fenced lines in both pages start with ``bazelisk``."""
        for path in (PAGE, GENERATED):
            fenced, _ = _fenced_and_spans(path.read_text(encoding="utf-8"))
            offenders = [line for line in fenced if not line.startswith("bazelisk ")]
            assert offenders == [], f"{path}: {offenders}"

    def test_no_backticked_command_names_a_raw_script(self) -> None:
        """A backticked span that looks like a command uses ``bazelisk`` too."""
        for path in (PAGE, GENERATED):
            _, spans = _fenced_and_spans(path.read_text(encoding="utf-8"))
            offenders = [
                span
                for span in spans
                if _looks_like_command(span) and not span.startswith("bazelisk ")
            ]
            assert offenders == [], f"{path}: {offenders}"

    def test_repo_guard_reports_nothing(self) -> None:
        """``tests/bazel_docs.py`` finds no raw door in any of the three files."""
        assert bazel_docs.findings(ROOT, list(SWEPT_PATHS)) == []


class TestAscii:
    """The tier pages and the generator stay plain ASCII."""

    @pytest.mark.parametrize("relative", SWEPT_PATHS)
    def test_files_are_ascii(self, relative: str) -> None:
        """No confusable Unicode reaches a committed tier file."""
        text = (ROOT / relative).read_text(encoding="utf-8")
        offenders = sorted({hex(ord(char)) for char in text if ord(char) > 127})
        assert offenders == [], f"{relative}: {offenders}"


class TestMain:
    """``main`` writes once, then leaves the file byte-identical."""

    def test_main_is_idempotent(
        self,
        gen: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A second run writes the same bytes and says so."""
        out = tmp_path / "nested" / "tier.md"
        monkeypatch.delenv(gen.CATALOG_ENV, raising=False)
        assert gen.main(["--out", str(out)]) == 0
        first = out.read_bytes()
        assert first
        assert gen.main(["--out", str(out)]) == 0
        assert out.read_bytes() == first
        assert "up to date" in capsys.readouterr().out

    def test_main_reads_the_env_override(
        self, gen: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``EZ_NVIDIA_LAB_CATALOG`` points the reader at another catalog."""
        path = _write_catalog(tmp_path, _catalog_payload([_tool_payload("from-env")]))
        out = tmp_path / "tier.md"
        monkeypatch.setenv(gen.CATALOG_ENV, str(path))
        assert gen.main(["--out", str(out)]) == 0
        assert "`from-env`" in out.read_text(encoding="utf-8")

    def test_cli_catalog_flag_beats_the_env(
        self, gen: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``--catalog`` wins over the environment variable."""
        flagged = _write_catalog(tmp_path, _catalog_payload([_tool_payload("flagged")]))
        monkeypatch.setenv(gen.CATALOG_ENV, str(tmp_path / "absent.json"))
        catalog = gen.load_catalog(gen.resolve_catalog_path(str(flagged)))
        assert [tool.tool_id for tool in catalog.tools] == ["flagged"]
        out = tmp_path / "tier.md"
        assert gen.main(["--catalog", str(flagged), "--out", str(out)]) == 0
        assert "`flagged`" in out.read_text(encoding="utf-8")

    def test_paths_resolve_to_the_repo_defaults(self, gen: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
        """With no flag and no env the reader and the writer use the repo paths."""
        monkeypatch.delenv(gen.CATALOG_ENV, raising=False)
        assert gen.resolve_catalog_path(None) == gen.DEFAULT_CATALOG_PATH
        assert gen.resolve_output_path(None) == gen.OUTPUT_FILE

    def test_script_entry_point(self, gen: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Running the file as a script publishes the page and exits zero."""
        out = tmp_path / "tier.md"
        monkeypatch.delenv(gen.CATALOG_ENV, raising=False)
        monkeypatch.setattr(sys, "argv", [str(GEN_PY), "--out", str(out)])
        with pytest.raises(SystemExit) as caught:
            runpy.run_path(str(GEN_PY), run_name="__main__")
        assert caught.value.code == 0
        assert out.is_file()
