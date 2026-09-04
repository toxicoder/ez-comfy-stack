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


def test_conventions_document_sticky_header() -> None:
    """Docs publish notes the sticky-tabs contract for later edits."""
    text = _read(CONVENTIONS)
    assert "navigation.tabs.sticky" in text
    assert "header.autohide" in text
    assert "stylesheets/extra.css" in text
