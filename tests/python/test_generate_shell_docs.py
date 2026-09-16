"""Hermetic tests for docs/generate_shell_docs.py.

Stdlib + the generator module. No MkDocs, Docker, or network.
"""

from __future__ import annotations

import importlib.util
import sys
from io import StringIO
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
GEN_PY = ROOT / "docs" / "generate_shell_docs.py"
OUTPUT = ROOT / "docs" / "generated" / "shell" / "reference.md"
MANAGE = ROOT / "scripts" / "manage.sh"


def _load() -> Any:
    """Load docs/generate_shell_docs.py as a module.

    Returns:
        Loaded generator module.
    """
    spec = importlib.util.spec_from_file_location("ez_generate_shell_docs", GEN_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ez_generate_shell_docs"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def gen() -> Any:
    """Loaded generator module."""
    return _load()


def _write_script(tmp_path: Path, body: str) -> Path:
    """Write a temporary .sh file.

    Args:
        tmp_path: Pytest tmp directory.
        body: File contents.

    Returns:
        Path to the written script.
    """
    path = tmp_path / "sample.sh"
    path.write_text(body, encoding="utf-8")
    return path


def test_section_and_body(gen: Any, tmp_path: Path) -> None:
    """``##`` markers produce a section heading with formatted body text."""
    path = _write_script(
        tmp_path,
        "# ## My Section\n# body line 1\n# body line 2\n\nsome code\n",
    )
    docs = gen.extract_from_file(path)
    assert len(docs) == 1
    assert "## My Section" in docs[0]
    assert "body line 1" in docs[0]


def test_command_marker(gen: Any, tmp_path: Path) -> None:
    """``@command`` markers produce a command heading and description body."""
    path = _write_script(
        tmp_path,
        "# @command start\n# Type yes. Headroom preflight.\ncmd_start() { :; }\n",
    )
    docs = gen.extract_from_file(path)
    assert len(docs) == 1
    assert "Command: start" in docs[0]
    assert "Type yes" in docs[0]


def test_function_marker_only(gen: Any, tmp_path: Path) -> None:
    """Functions are documented only when ``@function`` is present."""
    path = _write_script(
        tmp_path,
        "# helper docs without marker\n"
        "csv_lines() { :; }\n"
        "# @function cmd_status\n"
        "# Read-only status.\n"
        "cmd_status() { :; }\n",
    )
    docs = gen.extract_from_file(path)
    joined = "\n".join(docs)
    assert "Function `cmd_status`" in joined
    assert "Read-only status" in joined
    assert "csv_lines" not in joined


def test_skips_google_hash_banners(gen: Any, tmp_path: Path) -> None:
    """Google ``#####`` banners do not leak into the command body."""
    path = _write_script(
        tmp_path,
        "# @command doctor\n"
        "#######################################\n"
        "# Preflight: Docker, GPU, RAM/disk.\n"
        "# Globals:\n"
        "#   MODELS_DIR\n"
        "#######################################\n"
        "cmd_doctor() { :; }\n",
    )
    docs = gen.extract_from_file(path)
    assert "#####" not in docs[0]
    assert "Preflight" in docs[0]
    assert "MODELS_DIR" in docs[0]


def test_subsection_nests_in_parent(gen: Any, tmp_path: Path) -> None:
    """``###`` subsections nest inside the previous ``##`` block."""
    path = _write_script(
        tmp_path,
        "# ## Parent\n# intro\n# ### Child\n# child body\n",
    )
    docs = gen.extract_from_file(path)
    assert "### Child" in docs[0]
    assert "child body" in docs[0]


def test_preserves_session_vars(gen: Any, tmp_path: Path) -> None:
    """Session variables stay ``${VAR}`` — never lab placeholders."""
    path = _write_script(
        tmp_path,
        "# ## Example\n"
        "# Usage:\n"
        "#   ./scripts/manage.sh status\n"
        "# Open http://${SPARK_HOST}:${COMFY_PORT}\n",
    )
    docs = gen.extract_from_file(path)
    assert "${SPARK_HOST}" in docs[0]
    assert "${COMFY_PORT}" in docs[0]
    assert "{{PLACEHOLDER}}" not in docs[0]


def test_safety_becomes_admonition(gen: Any) -> None:
    """Safety lines become warning admonitions."""
    out = gen._format_body(["Safety: type yes on start.", "Usage:", "./scripts/manage.sh start"])
    assert "!!! warning" in out
    assert "```bash" in out
    assert "./scripts/manage.sh start" in out


def test_empty_body(gen: Any) -> None:
    """Empty or whitespace-only bodies format to an empty string."""
    assert gen._format_body([]) == ""
    assert gen._format_body([""]) == ""


def test_collapse_blank_lines(gen: Any) -> None:
    """Generated pages keep at most one blank line between blocks."""
    text = gen._collapse_blank_lines("a\n\n\n\nb\n")
    assert text == "a\n\nb\n"
    assert not text.endswith("\n\n")


def test_render_collapses_comment_blank_runs(gen: Any, tmp_path: Path) -> None:
    """Comment bodies with extra blanks do not emit triple newlines."""
    path = _write_script(
        tmp_path,
        "# ## tool\n# Overview.\n#\n#\n# Still overview.\n",
    )
    text = gen.render_reference([path])
    assert "\n\n\n" not in text
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_render_includes_page_chrome(gen: Any, tmp_path: Path) -> None:
    """Rendered page has required docs chrome and a source comment."""
    path = _write_script(tmp_path, "# ## tool\n# Overview.\n# @command status\n# Read-only.\n")
    text = gen.render_reference([path])
    assert text.startswith("---")
    assert "title:" in text
    assert "**What's on this page**" in text
    assert "**What this enables**" in text
    assert "Command: status" in text
    assert "{{PLACEHOLDER}}" not in text


def test_render_rejects_lab_placeholders(gen: Any, tmp_path: Path) -> None:
    """Lab ``{{PLACEHOLDER}}`` tokens are a generator error."""
    path = _write_script(
        tmp_path,
        "# ## Example\n# host: {{PLACEHOLDER}}\n",
    )
    with pytest.raises(ValueError, match="PLACEHOLDER"):
        gen.render_reference([path])


def test_render_fallback_when_empty(gen: Any, tmp_path: Path) -> None:
    """An empty scan list still emits chrome plus the no-docs note."""
    empty = tmp_path / "none.sh"
    empty.write_text("echo hi\n", encoding="utf-8")
    text = gen.render_reference([empty])
    assert "_No structured comments found yet._" in text
    assert "**What's on this page**" in text


def test_main_writes_and_skips_unchanged(gen: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``main()`` writes once, then reports up to date without ``--force``."""
    out = tmp_path / "reference.md"
    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gen, "OUTPUT_FILE", out)
    assert gen.main(["--force"]) == 0
    assert out.is_file()
    first = out.read_text(encoding="utf-8")
    assert "Generated shell reference" in first
    buf = StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    assert gen.main([]) == 0
    assert "up to date" in buf.getvalue()
    assert out.read_text(encoding="utf-8") == first


def test_committed_reference_matches_generator(gen: Any) -> None:
    """Committed generated page equals a fresh in-process render."""
    assert OUTPUT.is_file(), "commit docs/generated/shell/reference.md"
    expected = gen.render_reference()
    actual = OUTPUT.read_text(encoding="utf-8")
    assert actual == expected


def test_manage_public_verbs_have_command_markers() -> None:
    """Every public manage.sh case verb has ``# @command <verb>`` (except banned H3)."""
    text = MANAGE.read_text(encoding="utf-8")
    verbs = _manage_case_verbs(text)
    missing = [verb for verb in verbs if f"# @command {verb}" not in text]
    assert missing == [], "manage.sh missing # @command:\n" + "\n".join(missing)


def _manage_case_verbs(text: str) -> list[str]:
    """Parse public verbs from manage.sh ``case`` (skip banned H3 aliases).

    Args:
        text: manage.sh source.

    Returns:
        Unique verb names in case order.
    """
    banned = {"download-h3", "queue-h3", "farm-h3", "stitch-h3"}
    verbs: list[str] = []
    in_case = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("case ") and "${cmd}" in stripped:
            in_case = True
            continue
        if not in_case:
            continue
        if stripped.startswith("esac"):
            break
        if ")" not in stripped or stripped.startswith("*"):
            continue
        left = stripped.split(")", 1)[0]
        for part in left.split("|"):
            token = part.strip()
            if token in {"-h", "--help"}:
                continue
            if token in banned:
                continue
            if token and token not in verbs:
                verbs.append(token)
    return verbs
