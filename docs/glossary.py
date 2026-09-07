"""First-party glossary: JSON source, markdown render, HTML wrap, modal inject.

Designed for MkDocs hooks (``docs/hooks.py``) and hermetic pytest (stdlib
``json`` only — CI's test job does not install PyYAML).
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

PLACEHOLDER = "<!-- ez-glossary:render -->"

DEFAULT_GLOSSARY_PATH = (
    Path(__file__).resolve().parents[1] / "includes" / "glossary.json"
)

CATEGORY_ORDER = (
    "Models",
    "Modalities",
    "Studio",
    "Hardware and safety",
    "Film",
    "Audio",
    "Licenses",
)

_ID_RE = re.compile(r"^[a-z0-9-]+$")
_TOKEN_RE = re.compile(r"(<!--.*?-->|<[^>]+>)", re.DOTALL)
_TAG_NAME_RE = re.compile(r"^</?\s*([A-Za-z][A-Za-z0-9:-]*)")
_ARTICLE_RE = re.compile(
    r'(<article\b[^>]*class="[^"]*md-content__inner[^"]*"[^>]*>)(.*?)(</article>)',
    re.IGNORECASE | re.DOTALL,
)
_JSON_SCRIPT_RE = re.compile(
    r'<script type="application/json" id="ez-glossary-data">.*?</script>',
    re.DOTALL,
)

SKIP_TAGS = frozenset(
    {
        "a",
        "abbr",
        "button",
        "code",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "kbd",
        "label",
        "pre",
        "script",
        "summary",
        "style",
        "svg",
        "textarea",
    }
)
VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)
SKIP_CLASS_MARKERS = ("ez-term", "ez-docs-dev-banner", "ez-glossary-dialog")

_GLOSSARY_CACHE: dict[str, tuple["Term", ...]] = {}


@dataclass(frozen=True)
class Term:
    """One glossary entry.

    Attributes:
        id: URL fragment and ``data-term`` value (``[a-z0-9-]+``).
        title: Canonical heading on the glossary page.
        aliases: Match strings, longest-first at wrap time.
        category: Group heading on the glossary page.
        short: One-line definition for ``title=`` and the modal body.
        long: Markdown used on the glossary page only.
        see_also: Other term ids.
    """

    id: str
    title: str
    aliases: tuple[str, ...]
    category: str
    short: str
    long: str
    see_also: tuple[str, ...]


def relative_glossary_href(page_url: str, term_id: str) -> str:
    """Return a mike-safe relative link from this page to ``glossary/#id``.

    Args:
        page_url: MkDocs ``page.url`` (``learn/comfyui/``, ``""`` on Home).
        term_id: Glossary fragment.

    Returns:
        Relative href including the ``#`` fragment.
    """
    url = (page_url or "").replace("\\", "/")
    if url.endswith("index.html"):
        url = url[: -len("index.html")]
    url = url.strip("/")
    if not url:
        prefix = "glossary/"
    else:
        depth = url.count("/") + 1
        prefix = "../" * depth + "glossary/"
    return f"{prefix}#{term_id}"


def _term_from_mapping(raw: Any, index: int) -> Term:
    """Build a Term from one JSON object.

    Args:
        raw: Decoded JSON value.
        index: Zero-based list index (for error messages).

    Returns:
        Frozen Term.

    Raises:
        ValueError: Schema mismatch.
    """
    if not isinstance(raw, dict):
        raise ValueError(f"glossary[{index}] must be an object")
    term_id = raw.get("id")
    title = raw.get("title")
    aliases = raw.get("aliases")
    category = raw.get("category")
    short = raw.get("short")
    long = raw.get("long")
    see_also = raw.get("see_also") or []
    if not isinstance(term_id, str) or not _ID_RE.fullmatch(term_id):
        raise ValueError(f"glossary[{index}].id must match [a-z0-9-]+")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"glossary[{index}].title must be a non-empty string")
    if not isinstance(aliases, list) or not aliases or not all(
        isinstance(a, str) and a.strip() for a in aliases
    ):
        raise ValueError(f"glossary[{index}].aliases must be a non-empty string list")
    if not isinstance(category, str) or not category.strip():
        raise ValueError(f"glossary[{index}].category must be a non-empty string")
    if not isinstance(short, str) or not short.strip() or "\n" in short:
        raise ValueError(
            f"glossary[{index}].short must be a single-line non-empty string"
        )
    if not isinstance(long, str) or not long.strip():
        raise ValueError(f"glossary[{index}].long must be a non-empty string")
    if not isinstance(see_also, list) or not all(isinstance(s, str) for s in see_also):
        raise ValueError(f"glossary[{index}].see_also must be a list of strings")
    return Term(
        id=term_id,
        title=title.strip(),
        aliases=tuple(a.strip() for a in aliases),
        category=category.strip(),
        short=short.strip(),
        long=long.strip(),
        see_also=tuple(see_also),
    )


def validate_glossary(terms: Sequence[Term]) -> None:
    """Reject duplicate ids/aliases and dangling see_also.

    Args:
        terms: Glossary entries.

    Raises:
        ValueError: On the first invariant violation.
    """
    ids: set[str] = set()
    alias_owner: dict[str, str] = {}
    for term in terms:
        if term.id in ids:
            raise ValueError(f"duplicate id {term.id!r}")
        ids.add(term.id)
        for alias in term.aliases:
            key = alias.lower()
            if key in alias_owner:
                raise ValueError(
                    f"duplicate alias {alias!r} on {term.id} and {alias_owner[key]}"
                )
            alias_owner[key] = term.id
    for term in terms:
        for ref in term.see_also:
            if ref not in ids:
                raise ValueError(f"{term.id} see_also {ref!r} is not a term id")


def load_glossary(path: str | Path | None = None) -> tuple[Term, ...]:
    """Load and validate the shipped (or test) glossary JSON.

    Args:
        path: Override path. Default ``includes/glossary.json``.

    Returns:
        Immutable term tuple.

    Raises:
        ValueError: Invalid JSON schema.
        OSError: File unreadable.
    """
    resolved = Path(path) if path is not None else DEFAULT_GLOSSARY_PATH
    cache_key = str(resolved)
    cached = _GLOSSARY_CACHE.get(cache_key)
    if cached is not None:
        return cached
    raw = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("glossary JSON must be a list of term objects")
    terms = tuple(_term_from_mapping(item, i) for i, item in enumerate(raw))
    validate_glossary(terms)
    _GLOSSARY_CACHE[cache_key] = terms
    return terms


def _category_sort_key(category: str) -> tuple[int, str]:
    """Stable category order: known groups first, then alphabetical.

    Args:
        category: Category label.

    Returns:
        Sort tuple.
    """
    try:
        return (CATEGORY_ORDER.index(category), category.lower())
    except ValueError:
        return (len(CATEGORY_ORDER), category.lower())


def render_glossary_markdown(terms: Sequence[Term]) -> str:
    """Render glossary JSON as markdown sections (evaluated in on_page_markdown).

    Args:
        terms: Validated terms.

    Returns:
        Markdown fragment with ``{#id}`` headings.
    """
    grouped: dict[str, list[Term]] = {}
    for term in terms:
        grouped.setdefault(term.category, []).append(term)
    chunks: list[str] = []
    for category in sorted(grouped, key=_category_sort_key):
        chunks.append(f"## {category}")
        chunks.append("")
        for term in grouped[category]:
            chunks.append(f"### {term.title} {{#{term.id}}}")
            chunks.append("")
            chunks.append(term.long)
            chunks.append("")
            also = [a for a in term.aliases if a != term.title]
            if also:
                chunks.append("**Also called:** " + ", ".join(f"`{a}`" for a in also))
                chunks.append("")
            if term.see_also:
                by_id = {t.id: t for t in terms}
                links = " · ".join(
                    f"[{by_id[ref].title}](#{ref})" for ref in term.see_also
                )
                chunks.append(f"**See also:** {links}")
                chunks.append("")
        chunks.append("")
    return "\n".join(chunks).rstrip() + "\n"


def render_placeholder(markdown: str, terms: Sequence[Term] | None = None) -> str:
    """Replace ``PLACEHOLDER`` with rendered glossary markdown.

    Args:
        markdown: Page source.
        terms: Optional preloaded terms (tests). Default loads the shipped file.

    Returns:
        Markdown with the placeholder expanded, or unchanged if absent.
    """
    if PLACEHOLDER not in markdown:
        return markdown
    loaded = terms if terms is not None else load_glossary()
    return markdown.replace(PLACEHOLDER, render_glossary_markdown(loaded), 1)


def _alias_index(
    terms: Sequence[Term],
) -> tuple[re.Pattern[str], dict[str, Term]]:
    """Build a longest-first alias regex and lowercased lookup.

    Args:
        terms: Glossary entries.

    Returns:
        Compiled pattern capturing the alias, and alias-lower → Term.
    """
    lookup: dict[str, Term] = {}
    aliases: list[str] = []
    for term in terms:
        for alias in term.aliases:
            lookup[alias.lower()] = term
            aliases.append(alias)
    aliases.sort(key=len, reverse=True)
    inner = "|".join(re.escape(a) for a in aliases)
    pattern = re.compile(
        rf"(?<![A-Za-z0-9_])({inner})(?![A-Za-z0-9_])",
        re.IGNORECASE,
    )
    return pattern, lookup


def _render_span(raw: str, term: Term, href: str) -> str:
    """Wrap matched source text in a modal trigger span.

    Args:
        raw: Original matched text (casing preserved).
        term: Glossary term.
        href: Relative glossary href.

    Returns:
        HTML span.
    """
    return (
        '<span class="ez-term" tabindex="0" role="button" '
        'aria-haspopup="dialog" aria-expanded="false" '
        f'data-term="{html.escape(term.id, quote=True)}" '
        f'data-href="{html.escape(href, quote=True)}" '
        f'title="{html.escape(term.short, quote=True)}">{raw}</span>'
    )


def _wrap_text(
    text: str,
    pattern: re.Pattern[str],
    lookup: dict[str, Term],
    seen: set[str],
    page_url: str,
) -> str:
    """Wrap first wrappable occurrence of each term id in a text node.

    Args:
        text: Raw HTML text node.
        pattern: Combined alias regex.
        lookup: Lowercased alias → Term.
        seen: Term ids already wrapped on this page (mutated).
        page_url: MkDocs page URL for relative hrefs.

    Returns:
        Text node with zero or more spans inserted.
    """
    out: list[str] = []
    last = 0
    for match in pattern.finditer(text):
        out.append(text[last : match.start()])
        raw = match.group(1)
        term = lookup[raw.lower()]
        if term.id in seen:
            out.append(raw)
        else:
            seen.add(term.id)
            out.append(_render_span(raw, term, relative_glossary_href(page_url, term.id)))
        last = match.end()
    out.append(text[last:])
    return "".join(out)


def _tag_name(token: str) -> str | None:
    """Return the lowercased tag name for an HTML tag token.

    Args:
        token: ``<tag ...>`` / ``</tag>`` fragment.

    Returns:
        Tag name, or None for comments / non-tags.
    """
    match = _TAG_NAME_RE.match(token)
    if match is None:
        return None
    return match.group(1).lower()


def _is_closing(token: str) -> bool:
    """True when ``token`` is a closing tag.

    Args:
        token: Tag fragment.

    Returns:
        Whether the tag closes an element.
    """
    return token.startswith("</")


def _is_self_closing(token: str, name: str) -> bool:
    """True for void / self-closing tags that must not push the skip stack.

    Args:
        token: Tag fragment.
        name: Lowercased tag name.

    Returns:
        Whether the tag does not wrap children.
    """
    stripped = token.rstrip()
    return stripped.endswith("/>") or name in VOID_TAGS


def _has_skip_class(token: str) -> bool:
    """True when an opening tag already carries glossary/banner classes.

    Args:
        token: Tag fragment.

    Returns:
        Whether descendants should be skipped.
    """
    lower = token.lower()
    return any(marker in lower for marker in SKIP_CLASS_MARKERS)


def _wrap_fragment(
    html_fragment: str,
    pattern: re.Pattern[str],
    lookup: dict[str, Term],
    seen: set[str],
    page_url: str,
) -> str:
    """Wrap text nodes in a fragment, skipping protected tags.

    Args:
        html_fragment: HTML (article inner or whole document).
        pattern: Combined alias regex.
        lookup: Lowercased alias → Term.
        seen: Term ids already wrapped (mutated).
        page_url: MkDocs page URL.

    Returns:
        Fragment with spans inserted in eligible text nodes.
    """
    skip_stack: list[str] = []
    pieces: list[str] = []
    for token in _TOKEN_RE.split(html_fragment):
        if not token:
            continue
        if token.startswith("<!--"):
            pieces.append(token)
            continue
        if token.startswith("<"):
            name = _tag_name(token)
            if name is not None:
                if _is_closing(token):
                    if skip_stack and skip_stack[-1] == name:
                        skip_stack.pop()
                elif not _is_self_closing(token, name):
                    if name in SKIP_TAGS or _has_skip_class(token):
                        skip_stack.append(name)
            pieces.append(token)
            continue
        if skip_stack:
            pieces.append(token)
        else:
            pieces.append(_wrap_text(token, pattern, lookup, seen, page_url))
    return "".join(pieces)


def wrap_html(
    document: str,
    terms: Sequence[Term],
    page_url: str = "",
) -> str:
    """Wrap the first occurrence of each term in article (or whole) HTML.

    Args:
        document: Rendered HTML page.
        terms: Validated terms.
        page_url: MkDocs ``page.url``.

    Returns:
        HTML with ``span.ez-term`` inserted.
    """
    if not terms:
        return document
    pattern, lookup = _alias_index(terms)
    seen: set[str] = set()
    match = _ARTICLE_RE.search(document)
    if match is None:
        return _wrap_fragment(document, pattern, lookup, seen, page_url)
    inner = _wrap_fragment(match.group(2), pattern, lookup, seen, page_url)
    return document[: match.start()] + match.group(1) + inner + match.group(3) + document[
        match.end() :
    ]


def _terms_payload(terms: Sequence[Term]) -> dict[str, dict[str, Any]]:
    """JSON object keyed by term id for the modal script.

    Args:
        terms: Glossary entries.

    Returns:
        Serializable mapping.
    """
    return {
        term.id: {
            "title": term.title,
            "short": term.short,
            "see_also": list(term.see_also),
        }
        for term in terms
    }


def inject_glossary_assets(document: str, terms: Sequence[Term]) -> str:
    """Append JSON data + ``<dialog>`` once (before ``</body>`` when present).

    Args:
        document: HTML that already contains ``span.ez-term``.
        terms: Glossary entries (full payload; JS looks up by id).

    Returns:
        HTML with assets injected, or unchanged if already present.
    """
    if 'id="ez-glossary-data"' in document:
        return document
    payload = json.dumps(_terms_payload(terms), ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c")
    blob = (
        '<script type="application/json" id="ez-glossary-data">'
        f"{payload}</script>\n"
        '<dialog class="ez-glossary-dialog" id="ez-glossary-dialog" '
        'aria-labelledby="ez-glossary-title">'
        '<div class="ez-glossary-dialog__panel">'
        '<button type="button" class="ez-glossary-dialog__close" '
        'id="ez-glossary-close" aria-label="Close definition">Close</button>'
        '<h2 class="ez-glossary-dialog__title" id="ez-glossary-title"></h2>'
        '<p class="ez-glossary-dialog__body" id="ez-glossary-body"></p>'
        '<p class="ez-glossary-dialog__see" id="ez-glossary-see" hidden></p>'
        '<p class="ez-glossary-dialog__more">'
        '<a class="ez-glossary-dialog__link" id="ez-glossary-link" href="#">'
        "Open full glossary entry</a></p>"
        "</div></dialog>\n"
    )
    lower = document.lower()
    idx = lower.rfind("</body>")
    if idx == -1:
        return document + blob
    return document[:idx] + blob + document[idx:]


def _page_src(page: Any) -> str:
    """MkDocs page source path, or empty.

    Args:
        page: Optional MkDocs page object.

    Returns:
        ``file.src_path`` with forward slashes.
    """
    if page is None:
        return ""
    src = getattr(getattr(page, "file", None), "src_path", "") or ""
    return str(src).replace("\\", "/")


def _page_url(page: Any) -> str:
    """MkDocs page.url, or empty.

    Args:
        page: Optional MkDocs page object.

    Returns:
        URL string.
    """
    if page is None:
        return ""
    return str(getattr(page, "url", "") or "")


def apply_glossary(
    document: str,
    page: Any = None,
    *,
    page_url: str | None = None,
    terms: Sequence[Term] | None = None,
) -> str:
    """Wrap terms and inject modal assets unless this is the glossary page.

    Args:
        document: Rendered HTML.
        page: Optional MkDocs page (src_path + url).
        page_url: Explicit URL override for tests.
        terms: Optional preloaded terms.

    Returns:
        HTML, possibly with spans + dialog.
    """
    src = _page_src(page)
    if src.endswith("glossary.md") or src.endswith("glossary/index.md"):
        return document
    url = page_url if page_url is not None else _page_url(page)
    loaded: Iterable[Term] = terms if terms is not None else load_glossary()
    loaded_seq = tuple(loaded)
    wrapped = wrap_html(document, loaded_seq, page_url=url)
    if 'class="ez-term"' not in wrapped:
        return wrapped
    return inject_glossary_assets(wrapped, loaded_seq)
