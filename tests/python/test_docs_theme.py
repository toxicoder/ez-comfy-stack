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
    """Table thead stays under the sticky header; wrap does not steal the scrollport."""
    css = _read(EXTRA_CSS)
    assert re.search(
        r"thead\s+th\s*\{[^}]*position:\s*sticky",
        css,
        re.S,
    )
    assert "--ez-sticky-table-top" in css
    assert "4.8rem" in css
    assert "4.2rem" in css
    assert re.search(
        r"html:has\(\.md-header__title--active\)\s*\{[^}]*--ez-sticky-table-top:\s*4\.2rem",
        css,
        re.S,
    )
    assert re.search(
        r"thead\s+th\s*\{[^}]*background-color:\s*var\(--md-default-bg-color\)",
        css,
        re.S,
    )
    assert re.search(
        r"\.md-typeset__scrollwrap\s*\{[^}]*overflow:\s*visible",
        css,
        re.S,
    )
    assert re.search(
        r"thead\s+th\s*\{[^}]*z-index:\s*[12]\b",
        css,
        re.S,
    )


def test_conventions_document_sticky_header() -> None:
    """Docs publish notes the sticky-tabs contract for later edits."""
    text = _read(CONVENTIONS)
    assert "navigation.tabs.sticky" in text
    assert "header.autohide" in text
    assert "stylesheets/extra.css" in text
    assert "0.875rem" in text
    assert "thead" in text
    assert "sticky table" in text.lower() or "table header" in text.lower()
