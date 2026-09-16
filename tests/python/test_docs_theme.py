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
PUBLISHED_JS = ROOT / "docs" / "javascripts" / "published.js"
CONVENTIONS = ROOT / "docs" / "project-conventions.md"
DOCS_STYLE = ROOT / "docs" / "contribute" / "docs-style.md"
TROUBLE_DOCS_SITE = ROOT / "docs" / "operate" / "troubleshooting-docs-site.md"


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
    assert "javascripts/published.js" in text
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


def test_extra_css_adopts_spark_lab_code_block_text() -> None:
    """Fenced blocks match spark-lab padding/radius/line-height; pygments stay colored."""
    css = _read(EXTRA_CSS)
    fenced = re.search(
        r"\.md-typeset pre\s*>\s*code\s*\{[^}]+\}",
        css,
        re.S,
    )
    assert fenced is not None, "missing .md-typeset pre > code rule"
    body = fenced.group(0)
    assert re.search(r"padding:\s*0\.9em 1\.05em", body)
    assert re.search(r"border-radius:\s*0\.25rem", body)
    assert re.search(r"line-height:\s*1\.55", body)

    inline_box = re.search(
        r"\.md-typeset code\s*\{[^}]+\}",
        css,
        re.S,
    )
    assert inline_box is not None, "missing .md-typeset code rule"
    box = inline_box.group(0)
    assert re.search(r"border-radius:\s*0\.2rem", box)
    assert re.search(r"padding:\s*0\.05em 0\.35em", box)

    assert re.search(
        r"\.md-typeset p code,\s*"
        r"\.md-typeset li code,\s*"
        r"\.md-typeset td code,\s*"
        r"\.md-typeset :not\(pre\)\s*>\s*code\s*\{[^}]*"
        r"color:\s*rgb\(\s*134,\s*183,\s*55\s*\)",
        css,
        re.S,
    )
    assert re.search(
        r"pre\s*>\s*code\s*\{[^}]*color:\s*rgb\(\s*134,\s*183,\s*55\s*\)",
        css,
        re.S,
    ) is None


def test_mkdocs_wires_spark_lab_code_font_and_highlight() -> None:
    """Roboto Mono + Material highlight line spans stay explicit."""
    text = _read(MKDOCS_YML)
    assert re.search(r"^  font:\s*$", text, re.M)
    assert re.search(r"^    code:\s*Roboto Mono\s*$", text, re.M)
    assert re.search(r"^      anchor_linenums:\s*true\s*$", text, re.M)
    assert re.search(r"^      line_spans:\s*__span\s*$", text, re.M)
    assert re.search(r"^      pygments_lang_class:\s*true\s*$", text, re.M)


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


def test_extra_css_floating_table_hscroll() -> None:
    """H-scroll mirror is position:fixed under the navbar z-index, not sticky."""
    css = _read(EXTRA_CSS)
    assert re.search(
        r"\.ez-table-hscroll\s*\{[^}]*position:\s*fixed",
        css,
        re.S,
    )
    assert re.search(
        r"\.ez-table-hscroll\s*\{[^}]*z-index:\s*3\b",
        css,
        re.S,
    )
    assert re.search(
        r"\.ez-table-hscroll\s*\{[^}]*overflow-x:\s*auto",
        css,
        re.S,
    )
    assert ".ez-table-hscroll__inner" in css
    assert re.search(
        r"\.ez-table-hscroll\s*\{[^}]*position:\s*sticky",
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


def test_tables_js_floating_hscroll_and_header_pan() -> None:
    """Wide tall tables get a fixed h-scroll mirror; the pinned header pans with it."""
    js = _read(TABLES_JS)
    assert "ez-table-hscroll" in js
    assert "ez-table-hscroll__inner" in js
    assert "scrollWidth" in js
    assert "clientWidth" in js
    assert "scrollLeft" in js
    assert "translateX" in js
    assert "md-typeset__scrollwrap" in js
    assert "thead.style.position" not in js
    assert re.search(r"style\.position\s*=\s*['\"]sticky", js) is None


def test_tables_js_releases_pin_when_table_leaves_viewport() -> None:
    """Cloned header and h-scroll hide once the table is fully past the navbar."""
    js = _read(TABLES_JS)
    assert re.search(r"function\s+inStickyBand\s*\(", js)
    assert js.count("inStickyBand(") >= 3
    pin_fn = re.search(
        r"function\s+pinTable\s*\([^)]*\)\s*\{",
        js,
    )
    hscroll_fn = re.search(
        r"function\s+needsHScroll\s*\([^)]*\)\s*\{",
        js,
    )
    assert pin_fn is not None
    assert hscroll_fn is not None
    pin_start = pin_fn.start()
    hscroll_start = hscroll_fn.start()
    pin_body = js[pin_start:hscroll_start] if pin_start < hscroll_start else js[pin_start:]
    assert "inStickyBand(" in pin_body
    assert "overlay.hidden" in pin_body
    assert re.search(
        r"desired\s*\+\s*theadH\s*<=\s*pin|theadH\s*\+\s*desired\s*<=\s*pin",
        pin_body,
    )
    needs_end = js.find("function placeHScroll", hscroll_start)
    needs_body = js[hscroll_start:needs_end] if needs_end > hscroll_start else js[hscroll_start:]
    assert "inStickyBand(" in needs_body


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
    assert "ez-table-hscroll" in text
    assert "scrollLeft" in text
    assert "inStickyBand" in text or "scrolled past" in text.lower()
    assert ".md-header" in text or "md-header" in text
    assert "ez-published-chip" in text
    assert "EZ_DOCS_PUBLISHED_AT" in text
    assert "Last published" in text or "last published" in text.lower()


def test_conventions_document_spark_lab_code_text() -> None:
    """Docs publish and style pages keep the spark-lab code contract."""
    text = _read(CONVENTIONS)
    assert "1.55" in text
    assert "rgb(134, 183, 55)" in text
    assert "Roboto Mono" in text
    assert "pre > code" in text or "pre > code" in text.replace("`", "")
    style = _read(DOCS_STYLE)
    assert "1.55" in style
    assert "rgb(134, 183, 55)" in style
    assert "Roboto Mono" in style
    assert "ez-table-hscroll" in style or "horizontal" in style.lower()
    assert "tables.js" in style


def test_troubleshooting_docs_site_covers_table_chrome() -> None:
    """Docs-site troubleshooting names a hard-refresh when table JS is stale."""
    text = _read(TROUBLE_DOCS_SITE)
    assert "tables.js" in text
    assert "hard-refresh" in text.lower() or "Hard-refresh" in text
    assert "ez-table-hscroll" in text or "horizontal" in text.lower()
    assert "scrolled past" in text.lower()


def test_extra_css_styles_published_chip() -> None:
    """Published chip is a pill beside the title; label hides without display:none."""
    css = _read(EXTRA_CSS)
    assert re.search(
        r"\.ez-published-chip\s*\{[^}]*float:\s*right",
        css,
        re.S,
    )
    assert re.search(
        r"\.ez-published-chip\s*\{[^}]*border-radius:\s*999px",
        css,
        re.S,
    )
    assert "--md-primary-fg-color" in css
    assert ".ez-published-chip__label" in css
    assert re.search(r"clip:\s*rect\(0,\s*0,\s*0,\s*0\)", css)
    assert re.search(r"display\s*:\s*none", css) is None


def test_published_js_rewrites_relative_time() -> None:
    """published.js upgrades the chip time label; datetime stays the source."""
    js = _read(PUBLISHED_JS)
    assert "document$.subscribe" in js
    assert ".ez-published-chip time[datetime]" in js or "datetime" in js
    assert "just now" in js
    assert "minute" in js
    assert "hour" in js
    assert "day" in js
    assert "14" in js
    assert "textContent" in js
