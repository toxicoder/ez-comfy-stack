"""Docs theme chrome: sticky header tabs, no autohide.

Hermetic: stdlib only. Reads mkdocs.yml and docs/stylesheets/extra.css
without MkDocs, network, or a browser.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MKDOCS_YML = ROOT / "mkdocs.yml"
EXTRA_CSS = ROOT / "docs" / "stylesheets" / "extra.css"
TABLES_JS = ROOT / "docs" / "javascripts" / "tables.js"
CONVENTIONS = ROOT / "docs" / "project-conventions.md"


def _read(path: Path) -> str:
    """Return UTF-8 file text.

    Args:
        path: File that must exist.

    Returns:
        Entire file contents.
    """
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def test_mkdocs_enables_sticky_tabs_not_autohide() -> None:
    """Tabs stay in the sticky header; header.autohide stays off."""
    text = _read(MKDOCS_YML)
    assert "navigation.tabs" in text
    assert "navigation.tabs.sticky" in text
    assert re.search(r"^\s*-\s*header\.autohide\s*$", text, re.M) is None
    tabs_at = text.index("navigation.tabs")
    sticky_at = text.index("navigation.tabs.sticky")
    assert tabs_at < sticky_at


def test_mkdocs_wires_extra_css() -> None:
    """Compact-on-scroll stylesheet is registered with MkDocs."""
    text = _read(MKDOCS_YML)
    assert "extra_css:" in text
    assert "stylesheets/extra.css" in text
    assert "extra_javascript:" in text
    assert "javascripts/glossary.js" in text
    assert "javascripts/commands.js" in text
    assert "javascripts/tables.js" in text
    assert "content.tooltips" in text


def test_extra_css_compacts_header_without_hiding_chrome() -> None:
    """Scrolled header shrinks slightly; tabs and controls stay visible."""
    css = _read(EXTRA_CSS)
    assert ".md-header" in css
    assert ".md-tabs" in css
    assert ":has(.md-header__title--active)" in css
    assert ".md-tabs__item" in css
    assert ".md-header__title" in css
    assert "prefers-reduced-motion" in css

    assert re.search(r"display\s*:\s*none", css) is None
    assert re.search(r"visibility\s*:\s*hidden", css) is None
    assert "translateY(-100%" not in css.replace(" ", "")


def test_extra_css_bumps_typeset_font_not_html() -> None:
    """Article copy is slightly larger than Material 0.8rem; chrome is not."""
    css = _read(EXTRA_CSS)
    assert re.search(
        r"\.md-typeset\s*\{[^}]*font-size:\s*0\.875rem",
        css,
        re.S,
    )
    assert re.search(r"html\s*\{[^}]*font-size", css, re.S) is None


def test_extra_css_sticks_table_headers_under_tabs() -> None:
    """Cloned header overlay sits under the navbar; table is a real table box."""
    css = _read(EXTRA_CSS)
    assert re.search(
        r"\.ez-table-pin\s*\{[^}]*position:\s*fixed",
        css,
        re.S,
    )
    assert re.search(
        r"\.ez-table-pin\s*\{[^}]*z-index:\s*3\b",
        css,
        re.S,
    )
    assert re.search(
        r"\.ez-table-pin\s*\{[^}]*background-color:\s*var\(--md-default-bg-color\)",
        css,
        re.S,
    )
    assert re.search(
        r"thead\s+th\s*\{[^}]*position:\s*sticky",
        css,
        re.S,
    ) is None
    # Material display:inline-block + overflow:auto on the table is more
    # specific than the wrap's display:table and steals the scrollport.
    assert re.search(
        r"\.md-typeset table:not\(\[class\]\)\s*,\s*"
        r"html \.md-typeset__table table\s*\{[^}]*overflow:\s*visible",
        css,
        re.S,
    )
    assert re.search(
        r"\.md-typeset table:not\(\[class\]\)\s*,\s*"
        r"html \.md-typeset__table table\s*\{[^}]*display:\s*table",
        css,
        re.S,
    )
    assert re.search(
        r"thead\s+th\s*\{[^}]*transition:",
        css,
        re.S,
    ) is None


def test_tables_js_clamps_header_above_tail_rows() -> None:
    """tables.js measures .md-header and keeps last row + 25% of previous clear."""
    js = _read(TABLES_JS)
    assert "document$.subscribe" in js
    assert ".md-header" in js
    assert "getBoundingClientRect" in js
    assert "0.25" in js
    assert "ez-table-pin" in js
    assert "cloneNode" in js
    assert "aria-hidden" in js
    assert "requestAnimationFrame" in js
    assert "table:not([class])" in js
    assert "thead.style.position" not in js
    assert "thead" in js
    assert "scroll" in js
    assert "resize" in js


def test_conventions_document_sticky_header() -> None:
    """Docs publish notes the sticky-tabs contract for later edits."""
    text = _read(CONVENTIONS)
    assert "navigation.tabs.sticky" in text
    assert "header.autohide" in text
    assert "stylesheets/extra.css" in text
    assert "0.875rem" in text
    assert "thead" in text
    assert "sticky table" in text.lower() or "table header" in text.lower()
    assert "tables.js" in text
    assert "0.25" in text or "25%" in text
    assert "overflow" in text.lower()
    assert "ez-table-pin" in text or "clone" in text.lower()
    assert ".md-header" in text or "md-header" in text
