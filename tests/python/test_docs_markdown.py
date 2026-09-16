"""Markdown spacing contract for authored docs and generated shell reference.

Hermetic: stdlib. No MkDocs. Locks trailing whitespace, consecutive blank
lines, a single trailing newline, and blank lines around ATX headings and
column-0 fences/tables/admonitions (outside fenced code).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
CONVENTIONS = DOCS / "project-conventions.md"
DOCS_STYLE = DOCS / "contribute" / "docs-style.md"

_HEADING_RE = re.compile(r"^#{1,6} \S")
_TABLE_RE = re.compile(r"^\|")
_ADMON_RE = re.compile(r"^(!{3}|\?{3}) ")
_HTML_COMMENT_RE = re.compile(r"^<!-- .* -->$")
_FENCE_OPEN_RE = re.compile(r"^(`{3,}|~{3,})")


def _doc_paths() -> list[Path]:
    """Return authored docs pages plus CONTRIBUTING.md.

    Returns:
        Sorted markdown paths under docs/ and the repo-root contributing file.
    """
    pages = sorted(DOCS.rglob("*.md"))
    pages.append(CONTRIBUTING)
    return pages


def _fence_tick(line: str) -> str | None:
    """Return the fence marker if this line opens or closes a fence.

    Args:
        line: Raw markdown line.

    Returns:
        The backtick/tilde run, or None.
    """
    match = _FENCE_OPEN_RE.match(line)
    if match is None:
        return None
    return match.group(1)


def _spacing_issues(path: Path) -> list[str]:
    """Return human-readable spacing violations for one markdown file.

    Args:
        path: Markdown file.

    Returns:
        Issue strings prefixed with path:line.
    """
    rel = path.relative_to(ROOT).as_posix()
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    issues: list[str] = []
    if b"\r" in raw:
        issues.append(f"{rel}:1: CRLF line endings")
    if not text.endswith("\n"):
        issues.append(f"{rel}:eof: missing trailing newline")
    elif text.endswith("\n\n"):
        issues.append(f"{rel}:eof: extra trailing newline")
    lines = text.splitlines()
    blanks = 0
    for index, line in enumerate(lines):
        lineno = index + 1
        if line.endswith(" ") or line.endswith("\t"):
            issues.append(f"{rel}:{lineno}: trailing whitespace")
        if line.strip() == "":
            blanks += 1
            if blanks >= 2:
                issues.append(f"{rel}:{lineno}: consecutive blank lines")
        else:
            blanks = 0

    def prev_ok_for_block(index: int) -> bool:
        if index == 0:
            return True
        prev = lines[index - 1]
        if prev.strip() == "":
            return True
        if _HTML_COMMENT_RE.match(prev.strip()):
            return True
        return False

    def next_ok_for_block(index: int) -> bool:
        if index + 1 >= len(lines):
            return True
        nxt = lines[index + 1]
        return nxt.strip() == ""

    fence: str | None = None
    in_table = False
    for index, line in enumerate(lines):
        lineno = index + 1
        marker = _fence_tick(line)
        if fence is None:
            if marker is not None:
                if not prev_ok_for_block(index):
                    issues.append(f"{rel}:{lineno}: fence needs a blank line before it")
                fence = marker
                in_table = False
                continue
            if _HEADING_RE.match(line):
                if not prev_ok_for_block(index):
                    issues.append(f"{rel}:{lineno}: heading needs a blank line before it")
                if not next_ok_for_block(index):
                    issues.append(f"{rel}:{lineno}: heading needs a blank line after it")
            if _ADMON_RE.match(line) and not prev_ok_for_block(index):
                issues.append(f"{rel}:{lineno}: admonition needs a blank line before it")
            is_table = bool(_TABLE_RE.match(line))
            if is_table and not in_table:
                in_table = True
                if not prev_ok_for_block(index):
                    issues.append(f"{rel}:{lineno}: table needs a blank line before it")
            elif in_table and not is_table:
                in_table = False
                prev_line_index = index - 1
                if prev_line_index >= 0 and not next_ok_for_block(prev_line_index):
                    issues.append(
                        f"{rel}:{prev_line_index + 1}: table needs a blank line after it"
                    )
            continue
        if marker == fence:
            if not next_ok_for_block(index):
                issues.append(f"{rel}:{lineno}: fence needs a blank line after it")
            fence = None
    return issues


def test_docs_markdown_spacing() -> None:
    """Authored docs and CONTRIBUTING.md follow the spacing contract."""
    hits: list[str] = []
    for path in _doc_paths():
        hits.extend(_spacing_issues(path))
    assert hits == [], "markdown spacing issues:\n" + "\n".join(hits)


def test_conventions_document_markdown_spacing() -> None:
    """Style pages name the spacing contract so later edits keep it."""
    text = CONVENTIONS.read_text(encoding="utf-8")
    style = DOCS_STYLE.read_text(encoding="utf-8")
    assert "trailing whitespace" in text.lower()
    assert "blank line" in text.lower()
    assert "trailing whitespace" in style.lower() or "spacing" in style.lower()
