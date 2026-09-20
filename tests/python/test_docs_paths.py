"""docs_file resolves .mdx after the MkDocs-to-MDX rename.

Hermetic: stdlib + tmp_path.
"""

from __future__ import annotations

from pathlib import Path

from _docs_paths import docs_file


def test_docs_file_prefers_mdx_when_md_missing(tmp_path: Path) -> None:
    """Renamed pages keep working when tests still name the .md path."""
    md = tmp_path / "page.md"
    mdx = tmp_path / "page.mdx"
    mdx.write_text("x", encoding="utf-8")
    assert docs_file(md) == mdx


def test_docs_file_keeps_existing_md(tmp_path: Path) -> None:
    """Generated .md pages are not redirected."""
    md = tmp_path / "page.md"
    md.write_text("x", encoding="utf-8")
    assert docs_file(md) == md
