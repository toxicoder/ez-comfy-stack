"""Page-brief wrap for the required docs scan lists.

Turns the first ``What's on this page`` / ``What this enables`` pair after
the page ``h1`` into a two-column ``ez-page-brief`` card. Source markdown
stays bold + bullets; this module runs on rendered HTML from
``docs/hooks.py`` ``on_post_page``. Stdlib only (hermetic pytest).
"""

from __future__ import annotations

import html
import re

ON_PAGE_LABEL = "What's on this page"
ENABLES_LABEL = "What this enables"

_H1_RE = re.compile(r"<h1\b[^>]*>.*?</h1>", re.IGNORECASE | re.DOTALL)
_APOS = r"(?:'|&apos;|&#39;|&#x27;)"
_ON_PAGE_RE = re.compile(
    rf"<p(?:\s[^>]*)?>\s*<strong>\s*What{_APOS}s on this page\s*</strong>\s*</p>",
    re.IGNORECASE,
)
_ENABLES_RE = re.compile(
    r"<p(?:\s[^>]*)?>\s*<strong>\s*What this enables\s*</strong>\s*</p>",
    re.IGNORECASE,
)
_TAG_RE = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9]*)([^>]*)>", re.DOTALL)
_UL_OPEN_RE = re.compile(r"<ul\b[^>]*>", re.IGNORECASE)

# Material outline-style list and check icons (24 viewBox), same SVG
# contract as the last-published chip in docs/hooks.py.
_LIST_SVG = (
    '<svg class="ez-page-brief__icon" xmlns="http://www.w3.org/2000/svg" '
    'viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M4 10.5c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5 1.5-.67 '
    "1.5-1.5-.67-1.5-1.5-1.5zm0-6c-.83 0-1.5.67-1.5 1.5S3.17 7.5 4 "
    "7.5 5.5 6.83 5.5 6 4.83 4.5 4 4.5zm0 12c-.83 0-1.5.68-1.5 1.5s.68 "
    "1.5 1.5 1.5 1.5-.68 1.5-1.5-.67-1.5-1.5-1.5zM7 19h14v-2H7v2zm0-6h14v-2H7v2zm0-8v2h14V5H7z"
    '"></path></svg>'
)
_CHECK_SVG = (
    '<svg class="ez-page-brief__icon" xmlns="http://www.w3.org/2000/svg" '
    'viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 '
    "12 2m-2 15-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8z"
    '"></path></svg>'
)


def _skip_ws(html_text: str, start: int) -> int:
    """Return the index of the first non-whitespace character at or after start.

    Args:
        html_text: Rendered HTML.
        start: Index to begin scanning.

    Returns:
        Index of the next non-whitespace character, or ``len(html_text)``.
    """
    n = len(html_text)
    i = start
    while i < n and html_text[i].isspace():
        i += 1
    return i


def _match_label(html_text: str, start: int, pattern: re.Pattern[str]) -> int | None:
    """Match a labeled ``<p><strong>…</strong></p>`` after optional whitespace.

    Args:
        html_text: Rendered HTML.
        start: Index after the previous block.
        pattern: Label paragraph regex.

    Returns:
        Index after the matched paragraph, or ``None``.
    """
    i = _skip_ws(html_text, start)
    match = pattern.match(html_text, i)
    if match is None:
        return None
    return match.end()


def _read_ul(html_text: str, start: int) -> tuple[str, int] | None:
    """Read one ``<ul>…</ul>`` with depth counting so inner lists stay intact.

    Args:
        html_text: Rendered HTML.
        start: Index after the label paragraph.

    Returns:
        ``(ul_html, index_after)`` or ``None`` when the next block is not a list.
    """
    i = _skip_ws(html_text, start)
    if _UL_OPEN_RE.match(html_text, i) is None:
        return None
    depth = 0
    for match in _TAG_RE.finditer(html_text, i):
        slash = match.group(1)
        name = match.group(2).lower()
        rest = match.group(3)
        if name != "ul":
            continue
        self_close = rest.rstrip().endswith("/")
        if slash:
            depth -= 1
            if depth == 0:
                end = match.end()
                return html_text[i:end], end
        elif not self_close:
            depth += 1
    return None


def _title_html(icon: str, label: str) -> str:
    """Return the non-heading title row for one column.

    Args:
        icon: Inline SVG markup.
        label: Visible title text.

    Returns:
        HTML for ``ez-page-brief__title``.
    """
    return (
        f'<p class="ez-page-brief__title">{icon}'
        f'<span class="ez-page-brief__label">{html.escape(label, quote=False)}</span>'
        "</p>"
    )


def _render_card(on_page_ul: str, enables_ul: str) -> str:
    """Return the two-column page-brief card HTML.

    Args:
        on_page_ul: Rendered ``<ul>`` for What's on this page.
        enables_ul: Rendered ``<ul>`` for What this enables.

    Returns:
        HTML for ``.ez-page-brief``.
    """
    return (
        '<div class="ez-page-brief" role="region" aria-label="Page overview">'
        '<div class="ez-page-brief__col ez-page-brief__on-page">'
        f"{_title_html(_LIST_SVG, ON_PAGE_LABEL)}"
        f"{on_page_ul}"
        "</div>"
        '<div class="ez-page-brief__col ez-page-brief__enables">'
        f"{_title_html(_CHECK_SVG, ENABLES_LABEL)}"
        f"{enables_ul}"
        "</div>"
        "</div>"
    )


def wrap_page_brief(html_text: str) -> str:
    """Wrap the first page-brief pair after the first ``h1``.

    Idempotent: HTML that already contains ``class="ez-page-brief"`` is
    unchanged. A later prose mention of the class name does not skip wrap.
    Missing ``h1``, missing either labeled list, or extra nodes between the
    pair leaves the document unchanged. Trailing prose (``Who this is for``,
    ``hr``, next heading) stays outside the card.

    Args:
        html_text: Rendered HTML page (or article fragment).

    Returns:
        HTML with at most one page-brief card.
    """
    if 'class="ez-page-brief"' in html_text:
        return html_text
    h1 = _H1_RE.search(html_text)
    if h1 is None:
        return html_text
    cursor = h1.end()
    on_label_end = _match_label(html_text, cursor, _ON_PAGE_RE)
    if on_label_end is None:
        return html_text
    on_ul = _read_ul(html_text, on_label_end)
    if on_ul is None:
        return html_text
    on_html, after_on = on_ul
    enables_label_end = _match_label(html_text, after_on, _ENABLES_RE)
    if enables_label_end is None:
        return html_text
    enables_ul = _read_ul(html_text, enables_label_end)
    if enables_ul is None:
        return html_text
    enables_html, after_enables = enables_ul
    card = _render_card(on_html, enables_html)
    return html_text[:cursor] + card + html_text[after_enables:]
