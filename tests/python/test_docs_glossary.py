"""Glossary wrap, schema, modal wiring, and page chrome.

Hermetic: stdlib + the docs/glossary.py module. No MkDocs, network, or PyYAML.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GLOSSARY_PY = ROOT / "docs" / "glossary.py"
GLOSSARY_JSON = ROOT / "includes" / "glossary.json"
GLOSSARY_MD = ROOT / "docs" / "glossary.md"
GLOSSARY_JS = ROOT / "docs" / "javascripts" / "glossary.js"
EXTRA_CSS = ROOT / "docs" / "stylesheets" / "extra.css"
MKDOCS_YML = ROOT / "mkdocs.yml"
HOOKS_PY = ROOT / "docs" / "hooks.py"
DOCS = ROOT / "docs"


def _load_glossary_mod():
    """Load docs/glossary.py as a module.

    Returns:
        The loaded glossary module.
    """
    spec = importlib.util.spec_from_file_location("ez_docs_glossary", GLOSSARY_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ez_docs_glossary"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def gloss():
    """Loaded glossary module."""
    return _load_glossary_mod()


def _terms(gloss, rows: list[dict]) -> tuple:
    """Build Term tuples from dict rows.

    Args:
        gloss: Glossary module.
        rows: Mapping rows with id/title/aliases/category/short/long/see_also.

    Returns:
        Tuple of Term objects.
    """
    terms = []
    for row in rows:
        terms.append(
            gloss.Term(
                id=row["id"],
                title=row["title"],
                aliases=tuple(row["aliases"]),
                category=row["category"],
                short=row["short"],
                long=row.get("long", "Long form."),
                see_also=tuple(row.get("see_also", ())),
            )
        )
    return tuple(terms)


def _lab_terms(gloss) -> tuple:
    """Three lab terms with overlapping prefixes (LTX-2.5 vs LTX, Klein 4B vs Klein)."""
    return _terms(
        gloss,
        [
            {
                "id": "klein",
                "title": "Klein 4B",
                "aliases": ["Klein 4B", "Klein"],
                "category": "Models",
                "short": "Apache still-image model.",
                "see_also": ["wan"],
            },
            {
                "id": "wan",
                "title": "Wan 2.2",
                "aliases": ["Wan 2.2", "Wan"],
                "category": "Models",
                "short": "Apache silent motion model.",
            },
            {
                "id": "ltx",
                "title": "LTX-2.5",
                "aliases": ["LTX-2.5", "LTX"],
                "category": "Models",
                "short": "Joint AV model.",
            },
        ],
    )


def test_relative_href_index_and_nested(gloss) -> None:
    """mike-safe relative links from Home, a top page, and a nested Learn page."""
    assert gloss.relative_glossary_href("", "klein") == "glossary/#klein"
    assert gloss.relative_glossary_href("getting-started/", "klein") == (
        "../glossary/#klein"
    )
    assert gloss.relative_glossary_href("learn/comfyui/", "klein") == (
        "../../glossary/#klein"
    )
    assert gloss.relative_glossary_href("learn/", "klein") == "../glossary/#klein"


def test_wrap_longest_alias_wins(gloss) -> None:
    """LTX-2.5 is wrapped as one term, not an inner LTX plus leftover -2.5."""
    html = "<p>Queue LTX-2.5 after Klein 4B.</p>"
    out = gloss.wrap_html(html, _lab_terms(gloss), page_url="getting-started/")
    assert out.count("data-term=") == 2
    assert 'data-term="ltx"' in out
    assert "LTX-2.5" in out
    assert 'data-term="klein"' in out
    assert "-2.5" not in re.sub(r"LTX-2.5", "", out)


def test_wrap_word_boundary_skips_want(gloss) -> None:
    """Wan does not match inside Want."""
    html = "<p>Want a still? Use Wan next.</p>"
    out = gloss.wrap_html(html, _lab_terms(gloss), page_url="")
    assert out.count('data-term="wan"') == 1
    assert ">Wan<" in out or ">Wan</span>" in out
    assert "Want" in out
    assert re.search(r"data-term=\"wan\"[^>]*>Want", out) is None


def test_wrap_first_occurrence_only(gloss) -> None:
    """A second Klein on the same page stays plain text."""
    html = "<p>Klein 4B draft, then another Klein still.</p>"
    out = gloss.wrap_html(html, _lab_terms(gloss), page_url="")
    assert out.count('data-term="klein"') == 1
    assert "another Klein still" in out


def test_wrap_skips_code_pre_heading_and_links(gloss) -> None:
    """code, pre, headings, links, and tab labels are not wrapped; a later paragraph is."""
    html = (
        "<h2>Klein</h2>"
        "<p><code>Klein</code> and <pre>Wan</pre> and "
        '<a href="#">LTX-2.5</a></p>'
        "<label>Klein tab</label>"
        "<p>Then Klein in prose.</p>"
    )
    out = gloss.wrap_html(html, _lab_terms(gloss), page_url="")
    assert out.count('data-term="klein"') == 1
    assert "<h2>Klein</h2>" in out
    assert "<code>Klein</code>" in out
    assert "<pre>Wan</pre>" in out
    assert "<label>Klein tab</label>" in out
    assert ">Then " in out or "Then " in out


def test_wrap_only_inside_article_not_nav(gloss) -> None:
    """Material article is wrapped; a nav Klein is left alone."""
    html = (
        '<nav class="md-nav">Klein in nav</nav>'
        '<article class="md-content__inner md-typeset">'
        "<p>Klein in the article.</p>"
        "</article>"
    )
    out = gloss.wrap_html(html, _lab_terms(gloss), page_url="")
    assert out.count('data-term="klein"') == 1
    nav = out.split("<article")[0]
    assert "data-term=" not in nav


def test_wrap_preserves_original_casing(gloss) -> None:
    """Matched alias text is not rewritten to the canonical title."""
    html = "<p>Use klein 4B today.</p>"
    out = gloss.wrap_html(html, _lab_terms(gloss), page_url="")
    assert ">klein 4B</span>" in out


def test_wrap_sets_relative_href_and_title(gloss) -> None:
    """Span carries a relative glossary href and the short definition title."""
    html = "<p>Klein 4B is the still model.</p>"
    out = gloss.wrap_html(html, _lab_terms(gloss), page_url="learn/pipeline/")
    assert 'data-href="../../glossary/#klein"' in out
    assert 'title="Apache still-image model."' in out
    assert 'role="button"' in out
    assert 'aria-haspopup="dialog"' in out


def test_inject_dialog_once_when_terms_wrapped(gloss) -> None:
    """JSON payload + dialog appear once after wrap; skipped when nothing matched."""
    terms = _lab_terms(gloss)
    plain = "<html><body><p>No lab nouns here.</p></body></html>"
    assert "ez-glossary-data" not in gloss.apply_glossary(
        plain, page_url="", terms=terms
    )

    html = "<html><body><p>Klein 4B still.</p></body></html>"
    out = gloss.apply_glossary(html, page_url="getting-started/", terms=terms)
    assert out.count('id="ez-glossary-data"') == 1
    assert out.count("ez-glossary-dialog") >= 1
    payload = json.loads(
        re.search(
            r'<script type="application/json" id="ez-glossary-data">(.*?)</script>',
            out,
            re.DOTALL,
        ).group(1)
    )
    assert payload["klein"]["title"] == "Klein 4B"
    assert payload["klein"]["short"] == "Apache still-image model."
    assert payload["klein"]["see_also"] == ["wan"]


def test_skip_glossary_page(gloss) -> None:
    """glossary.md is not wrapped (the reader is already on the definitions)."""

    class _File:
        src_path = "glossary.md"

    class _Page:
        file = _File()
        url = "glossary/"

    html = "<article class='md-content__inner'><p>Klein 4B</p></article>"
    out = gloss.apply_glossary(html, page=_Page())
    assert "data-term=" not in out
    assert "ez-glossary-data" not in out


def test_render_placeholder_inserts_headings(gloss) -> None:
    """Placeholder becomes markdown headings with explicit ids."""
    md = "Intro\n\n<!-- ez-glossary:render -->\n"
    out = gloss.render_placeholder(md, terms=_lab_terms(gloss))
    assert "<!-- ez-glossary:render -->" not in out
    assert "### Klein 4B {#klein}" in out
    assert "### Wan 2.2 {#wan}" in out
    assert "## Models" in out


def test_validate_rejects_duplicate_alias(gloss) -> None:
    """Two terms may not share a case-insensitive alias."""
    terms = _terms(
        gloss,
        [
            {
                "id": "a",
                "title": "A",
                "aliases": ["Spark"],
                "category": "Hardware and safety",
                "short": "one",
            },
            {
                "id": "b",
                "title": "B",
                "aliases": ["spark"],
                "category": "Hardware and safety",
                "short": "two",
            },
        ],
    )
    with pytest.raises(ValueError, match="duplicate alias"):
        gloss.validate_glossary(terms)


def test_validate_rejects_unknown_see_also(gloss) -> None:
    """see_also must point at ids that exist."""
    terms = _terms(
        gloss,
        [
            {
                "id": "a",
                "title": "A",
                "aliases": ["A"],
                "category": "Models",
                "short": "one",
                "see_also": ["missing"],
            }
        ],
    )
    with pytest.raises(ValueError, match="see_also"):
        gloss.validate_glossary(terms)


def test_real_glossary_json_schema() -> None:
    """Shipped includes/glossary.json is unique, linked, and complete."""
    gloss = _load_glossary_mod()
    terms = gloss.load_glossary(GLOSSARY_JSON)
    assert len(terms) >= 50
    ids = [t.id for t in terms]
    assert len(ids) == len(set(ids))
    aliases_lower = []
    for term in terms:
        assert re.fullmatch(r"[a-z0-9-]+", term.id), term.id
        assert term.title.strip()
        assert term.aliases
        assert term.short.strip()
        assert "\n" not in term.short
        assert term.long.strip()
        assert term.category.strip()
        for alias in term.aliases:
            aliases_lower.append(alias.lower())
    assert len(aliases_lower) == len(set(aliases_lower))
    id_set = set(ids)
    for term in terms:
        for ref in term.see_also:
            assert ref in id_set, f"{term.id} see_also {ref!r}"


def test_rendered_glossary_lists_every_title() -> None:
    """glossary.md placeholder expands to every shipped title."""
    gloss = _load_glossary_mod()
    terms = gloss.load_glossary(GLOSSARY_JSON)
    text = GLOSSARY_MD.read_text(encoding="utf-8")
    assert gloss.PLACEHOLDER in text
    rendered = gloss.render_placeholder(text, terms=terms)
    for term in terms:
        assert f"{{#{term.id}}}" in rendered
        assert term.title in rendered


def test_mkdocs_wires_glossary_assets() -> None:
    """Theme features, JS, CSS, emoji, and watch path are registered."""
    text = MKDOCS_YML.read_text(encoding="utf-8")
    assert "content.tooltips" in text
    assert "search.highlight" in text
    assert "javascripts/glossary.js" in text
    assert "stylesheets/extra.css" in text
    assert "material.extensions.emoji.twemoji" in text
    assert "def_list" in text
    assert "watch:" in text
    assert "includes" in text
    assert "Learn:" in text
    assert "glossary.md" in text
    # Material abbr auto-append would double-wrap terms.
    assert "auto_append" not in text


def test_glossary_js_uses_native_dialog() -> None:
    """Modal script uses showModal and keyboard activation."""
    js = GLOSSARY_JS.read_text(encoding="utf-8")
    assert "showModal" in js
    assert "ez-term" in js
    assert "ez-glossary-dialog" in js
    assert "keydown" in js


def test_extra_css_styles_modal_without_hiding_header() -> None:
    """Glossary chrome is themed; header compact contract stays."""
    css = EXTRA_CSS.read_text(encoding="utf-8")
    assert ".ez-term" in css
    assert ".ez-glossary-dialog" in css
    assert "prefers-reduced-motion" in css
    assert re.search(r"display\s*:\s*none", css) is None


def test_hooks_source_calls_glossary() -> None:
    """hooks.py stamps first, then glossary render/wrap."""
    text = HOOKS_PY.read_text(encoding="utf-8")
    assert "render_placeholder" in text
    assert "apply_glossary" in text


def test_docs_pages_have_required_chrome() -> None:
    """Every docs markdown page keeps frontmatter and the two scan headings."""
    pages = sorted(DOCS.rglob("*.md"))
    assert pages
    missing: list[str] = []
    for path in pages:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        if not text.startswith("---"):
            missing.append(f"{rel}: missing YAML frontmatter")
            continue
        for needle in (
            "title:",
            "description:",
            "tags:",
            "**What's on this page**",
            "**What this enables**",
        ):
            if needle not in text:
                missing.append(f"{rel}: missing {needle!r}")
    assert missing == [], "docs chrome gaps:\n" + "\n".join(missing)
