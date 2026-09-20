"""Docs theme chrome: sticky header tabs, no autohide.

Hermetic: stdlib only. Reads docs-site theme files without Next, network,
or a browser.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAV_JSON = ROOT / "docs-site" / "lib" / "nav.json"
NAV_TS = ROOT / "docs-site" / "lib" / "nav.ts"
EXTRA_CSS = ROOT / "docs-site" / "app" / "global.css"
TABLES_TS = ROOT / "docs-site" / "components" / "table-chrome.tsx"
PUBLISHED_TS = ROOT / "docs-site" / "components" / "published-chip.tsx"
CONVENTIONS = ROOT / "docs" / "project-conventions.md"
DOCS_STYLE = ROOT / "docs" / "contribute" / "docs-style.md"
TROUBLE_DOCS_SITE = ROOT / "docs" / "operate" / "troubleshooting-docs-site.md"


def _read(path: Path) -> str:
    """Return UTF-8 file text, accepting a sibling ``.mdx`` after the codemod.

    Args:
        path: File that must exist, or its ``.mdx`` twin.

    Returns:
        Entire file contents.
    """
    if not path.is_file() and path.suffix == ".md":
        path = path.with_suffix(".mdx")
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def test_mkdocs_keeps_cinema_clip_pages_off_nav() -> None:
    """Technique encyclopedia pages are built but not listed in the sidebar."""
    nav = _read(NAV_JSON)
    ts = _read(NAV_TS)
    assert "generated/cinema/" in ts or "cinemaChildren" in ts
    assert "framing_shot_size/size_ecu" not in nav


def test_mkdocs_enables_sticky_tabs_not_autohide() -> None:
    """Tabs are root folders; no autohide chrome."""
    ts = _read(NAV_TS)
    assert "root: true" in ts
    css = _read(EXTRA_CSS)
    assert "translateY(-100%" not in css.replace(" ", "")


def test_mkdocs_wires_extra_css() -> None:
    """Voltage stylesheet and widgets live in the Fumadocs app."""
    css = _read(EXTRA_CSS)
    assert "--color-fd-primary: #c46e16" in css
    assert ".ez-table-pin" in css
    assert ".ez-spark-panel" in css
    assert TABLES_TS.is_file()
    assert PUBLISHED_TS.is_file()


def test_extra_css_compacts_header_without_hiding_chrome() -> None:
    """Voltage chrome stays visible; no display-none hide rules."""
    css = _read(EXTRA_CSS)
    assert "prefers-reduced-motion" in css
    assert re.search(r"display\s*:\s*none", css) is None
    assert re.search(r"visibility\s*:\s*hidden", css) is None
    assert "translateY(-100%" not in css.replace(" ", "")
    assert "indigo" not in css.lower()


def test_extra_css_bumps_typeset_font_not_html() -> None:
    """Article copy is 0.875rem; html font-size is not raised."""
    css = _read(EXTRA_CSS)
    assert re.search(
        r"article\s*\{[^}]*font-size:\s*0\.875rem",
        css,
        re.S,
    )
    assert re.search(r"html\s*\{[^}]*font-size", css, re.S) is None


def test_extra_css_adopts_spark_lab_code_block_text() -> None:
    """Fenced blocks keep padding/radius/line-height; inline code is terminal green."""
    css = _read(EXTRA_CSS)
    fenced = re.search(
        r"article pre\s*>\s*code\s*\{[^}]+\}",
        css,
        re.S,
    )
    assert fenced is not None, "missing article pre > code rule"
    body = fenced.group(0)
    assert re.search(r"padding:\s*0\.9em 1\.05em", body)
    assert re.search(r"border-radius:\s*0\.25rem", body)
    assert re.search(r"line-height:\s*1\.55", body)

    assert re.search(
        r"article p code,\s*"
        r"article li code,\s*"
        r"article td code,\s*"
        r"article :not\(pre\)\s*>\s*code\s*\{[^}]*"
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
    """Code blocks use the shared Voltage mono stack."""
    css = _read(EXTRA_CSS)
    assert "ui-monospace" in css or "--font-mono" in css


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
        r"\.ez-table-pin\s*\{[^}]*background-color:\s*var\(--color-fd-background\)",
        css,
        re.S,
    )
    assert re.search(
        r"thead\s+th\s*\{[^}]*position:\s*sticky",
        css,
        re.S,
    ) is None
    assert re.search(
        r"article table:not\(\[class\]\)\s*\{[^}]*overflow:\s*visible",
        css,
        re.S,
    )
    assert re.search(
        r"article table:not\(\[class\]\)\s*\{[^}]*display:\s*table",
        css,
        re.S,
    )


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
    """TableChrome measures the header and keeps last row + 25% of previous clear."""
    js = _read(TABLES_TS)
    assert "getBoundingClientRect" in js
    assert "0.25" in js
    assert "ez-table-pin" in js
    assert "cloneNode" in js
    assert "aria-hidden" in js
    assert "requestAnimationFrame" in js
    assert "table:not([class])" in js
    assert "thead" in js
    assert "scroll" in js
    assert "resize" in js


def test_tables_js_floating_hscroll_and_header_pan() -> None:
    """Wide tall tables get a fixed h-scroll mirror; the pinned header pans with it."""
    js = _read(TABLES_TS)
    assert "ez-table-hscroll" in js
    assert "ez-table-hscroll__inner" in js
    assert "scrollWidth" in js
    assert "clientWidth" in js
    assert "scrollLeft" in js
    assert "translateX" in js
    assert re.search(r"style\.position\s*=\s*['\"]sticky", js) is None


def test_tables_js_releases_pin_when_table_leaves_viewport() -> None:
    """Cloned header and h-scroll hide once the table is fully past the navbar."""
    js = _read(TABLES_TS)
    assert "inStickyBand" in js
    assert js.count("inStickyBand(") >= 2
    assert "overlay.hidden" in js


def test_conventions_document_sticky_header() -> None:
    """Docs publish notes the sticky-tabs contract for later edits."""
    text = _read(CONVENTIONS)
    assert "Fumadocs" in text or "docs-site" in text or "ez-table-pin" in text
    assert "0.875rem" in text
    assert "thead" in text
    assert "sticky table" in text.lower() or "table header" in text.lower()
    assert "ez-table-pin" in text or "table" in text.lower()
    assert "0.25" in text or "25%" in text or "ez-table-pin" in text
    assert "overflow" in text.lower()
    assert "ez-table-pin" in text or "clone" in text.lower()
    assert "ez-table-hscroll" in text
    assert "scrollLeft" in text
    assert "inStickyBand" in text or "scrolled past" in text.lower()
    assert "navbar" in text.lower() or "header" in text.lower()
    assert "ez-published-chip" in text
    assert "EZ_DOCS_PUBLISHED_AT" in text
    assert "Last published" in text or "last published" in text.lower()


def test_conventions_document_spark_lab_code_text() -> None:
    """Docs publish and style pages keep the spark-lab code contract."""
    text = _read(CONVENTIONS)
    assert "1.55" in text
    assert "rgb(134, 183, 55)" in text
    assert "Roboto Mono" in text or "monospace" in text
    assert "pre > code" in text or "pre > code" in text.replace("`", "")
    style = _read(DOCS_STYLE)
    assert "1.55" in style
    assert "rgb(134, 183, 55)" in style
    assert "ez-table-hscroll" in style or "horizontal" in style.lower()


def test_troubleshooting_docs_site_covers_table_chrome() -> None:
    """Docs-site troubleshooting names a hard-refresh when table JS is stale."""
    text = _read(TROUBLE_DOCS_SITE)
    assert "hard-refresh" in text.lower() or "Hard-refresh" in text or "table" in text.lower()
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
    assert "--color-fd-primary" in css
    assert ".ez-published-chip__label" in css
    assert re.search(r"clip:\s*rect\(0,\s*0,\s*0,\s*0\)", css)
    assert re.search(r"display\s*:\s*none", css) is None


def test_extra_css_cinema_clip_box() -> None:
    """Encyclopedia clips stay 16:9 and do not autoplay."""
    css = _read(EXTRA_CSS)
    assert ".ez-cinema-clip" in css
    assert ".ez-cinema-thumb" in css
    assert re.search(r"aspect-ratio:\s*16\s*/\s*9", css)
    assert re.search(
        r"\.ez-cinema-clip video\s*\{[^}]*width:\s*100%",
        css,
        re.S,
    )


def test_published_js_rewrites_relative_time() -> None:
    """PublishedChip upgrades the chip time label; datetime stays the source."""
    js = _read(PUBLISHED_TS)
    assert "datetime" in js
    assert "just now" in js
    assert "minute" in js
    assert "hour" in js
    assert "day" in js
    assert "14" in js
