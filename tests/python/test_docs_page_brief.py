"""Page-brief wrap: What's on this page / What this enables card.

Hermetic: stdlib + docs/page_brief.py and docs/hooks.py. No MkDocs.
"""

from __future__ import annotations

import html as html_lib
import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PAGE_BRIEF_PY = ROOT / "docs" / "page_brief.py"
HOOKS_PY = ROOT / "docs" / "hooks.py"
EXTRA_CSS = ROOT / "docs" / "stylesheets" / "extra.css"
CONVENTIONS = ROOT / "docs" / "project-conventions.md"
DOCS = ROOT / "docs"

CANONICAL = (
    "<h1 id='t'>Title</h1>"
    "<p><strong>What's on this page</strong></p>"
    "<ul>"
    "<li>Session variables and <code>manage.sh</code></li>"
    "<li>A <a href='../learn/'>learn</a> path</li>"
    "<li>Why you typed <em>yes</em> and a <strong>still-draft</strong></li>"
    "</ul>"
    "<p><strong>What this enables</strong></p>"
    "<ul>"
    "<li>A first still at <code>${COMFY_PORT}</code></li>"
    "</ul>"
    "<p><strong>Who this is for:</strong> operators.</p>"
    "<hr />"
    "<h2>Next</h2>"
)


def _load(path: Path, name: str):
    """Load a docs/*.py module by path.

    Args:
        path: Python file.
        name: Module name for sys.modules.

    Returns:
        Loaded module.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def brief():
    """Loaded page_brief module."""
    return _load(PAGE_BRIEF_PY, "ez_docs_page_brief")


@pytest.fixture
def hooks(monkeypatch: pytest.MonkeyPatch):
    """Loaded hooks module with no publish/version env.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        Loaded hooks module.
    """
    monkeypatch.delenv("MIKE_DOCS_VERSION", raising=False)
    monkeypatch.delenv("EZ_DOCS_VERSION", raising=False)
    monkeypatch.delenv("EZ_DOCS_GIT_REF", raising=False)
    monkeypatch.delenv("EZ_DOCS_PUBLISHED_AT", raising=False)
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    module = _load(HOOKS_PY, "ez_docs_hooks_page_brief")
    monkeypatch.setattr(
        module, "_git_head_committer_date", lambda: None, raising=False
    )
    return module


def test_wraps_canonical_pair(brief) -> None:
    """First labeled pair after h1 becomes one two-column region."""
    out = brief.wrap_page_brief(CANONICAL)
    assert out.count("ez-page-brief") >= 1
    assert 'role="region"' in out
    assert 'aria-label="Page overview"' in out
    assert "ez-page-brief__on-page" in out
    assert "ez-page-brief__enables" in out
    assert "What's on this page" in out
    assert "What this enables" in out
    assert "<svg" in out
    assert "aria-hidden=\"true\"" in out
    brief_at = out.index("ez-page-brief")
    h1_at = out.index("<h1")
    who_at = out.index("Who this is for")
    hr_at = out.index("<hr")
    h2_at = out.index("<h2")
    assert h1_at < brief_at < who_at < hr_at < h2_at
    assert "<p><strong>What's on this page</strong></p>" not in out
    assert "<p><strong>What this enables</strong></p>" not in out
    assert "<h2" not in out[brief_at:who_at]


def test_preserves_list_item_markup(brief) -> None:
    """Links, code, emphasis, and strong inside bullets stay intact."""
    out = brief.wrap_page_brief(CANONICAL)
    assert "<code>manage.sh</code>" in out
    assert "<a href='../learn/'>learn</a>" in out
    assert "<em>yes</em>" in out
    assert "<strong>still-draft</strong>" in out
    assert "<code>${COMFY_PORT}</code>" in out
    on_page = out[out.index("ez-page-brief__on-page") : out.index("ez-page-brief__enables")]
    enables = out[out.index("ez-page-brief__enables") :]
    assert "manage.sh" in on_page
    assert "COMFY_PORT" in enables
    assert "Who this is for" not in on_page
    assert "Who this is for" not in enables.split("</div>", 1)[0]


def test_nested_ul_stays_in_first_column(brief) -> None:
    """Depth-safe ul scan does not clip an inner list."""
    src = (
        "<h1>T</h1>"
        "<p><strong>What's on this page</strong></p>"
        "<ul><li>outer<ul><li>inner</li></ul></li></ul>"
        "<p><strong>What this enables</strong></p>"
        "<ul><li>outcome</li></ul>"
    )
    out = brief.wrap_page_brief(src)
    on_page = out[out.index("ez-page-brief__on-page") : out.index("ez-page-brief__enables")]
    assert "<li>inner</li>" in on_page
    assert on_page.count("<ul>") == 2
    assert on_page.count("</ul>") == 2
    assert "outcome" not in on_page


def test_leaves_who_this_is_for_outside(brief) -> None:
    """Trailing chrome after the second list is not swallowed."""
    out = brief.wrap_page_brief(CANONICAL)
    assert "<p><strong>Who this is for:</strong> operators.</p>" in out
    card_end = out.rindex("ez-page-brief")
    # Last class mention is inside the card; who-for follows the card close.
    assert out.index("Who this is for") > out.index("</div>", card_end)


def test_idempotent(brief) -> None:
    """A second wrap does not nest another card."""
    once = brief.wrap_page_brief(CANONICAL)
    twice = brief.wrap_page_brief(once)
    assert twice == once
    assert once.count('class="ez-page-brief"') == 1


def test_missing_enables_unchanged(brief) -> None:
    """One labeled list is not a page brief."""
    src = (
        "<h1>T</h1>"
        "<p><strong>What's on this page</strong></p>"
        "<ul><li>only</li></ul>"
        "<h2>Next</h2>"
    )
    assert brief.wrap_page_brief(src) == src


def test_pair_before_h1_unchanged(brief) -> None:
    """Chrome that is not after the first h1 is left alone."""
    src = (
        "<p><strong>What's on this page</strong></p>"
        "<ul><li>a</li></ul>"
        "<p><strong>What this enables</strong></p>"
        "<ul><li>b</li></ul>"
        "<h1>Late title</h1>"
    )
    assert brief.wrap_page_brief(src) == src


def test_no_h1_unchanged(brief) -> None:
    """Pages without an h1 are not wrapped."""
    src = (
        "<p><strong>What's on this page</strong></p>"
        "<ul><li>a</li></ul>"
        "<p><strong>What this enables</strong></p>"
        "<ul><li>b</li></ul>"
    )
    assert brief.wrap_page_brief(src) == src


def test_prose_mention_of_class_still_wraps(brief) -> None:
    """Documenting .ez-page-brief later on the page must not skip the card."""
    src = (
        "<h1>T</h1>"
        "<p><strong>What's on this page</strong></p>"
        "<ul><li>a</li></ul>"
        "<p><strong>What this enables</strong></p>"
        "<ul><li>b</li></ul>"
        "<p>Rendered as <code>.ez-page-brief</code>.</p>"
    )
    out = brief.wrap_page_brief(src)
    assert 'class="ez-page-brief"' in out
    assert "<code>.ez-page-brief</code>" in out
    assert out.count('class="ez-page-brief"') == 1


def test_apos_entity_label(brief) -> None:
    """HTML entity apostrophe in What's still matches."""
    src = (
        "<h1>T</h1>"
        "<p><strong>What&apos;s on this page</strong></p>"
        "<ul><li>a</li></ul>"
        "<p><strong>What this enables</strong></p>"
        "<ul><li>b</li></ul>"
    )
    out = brief.wrap_page_brief(src)
    assert "ez-page-brief" in out
    assert "What's on this page" in out


def test_titles_are_not_headings(brief) -> None:
    """Card titles must not become h2 (TOC pollution)."""
    out = brief.wrap_page_brief(CANONICAL)
    card = out[out.index("ez-page-brief") : out.index("Who this is for")]
    assert re.search(r"<h[1-6]\b", card) is None
    assert "ez-page-brief__title" in card


def _chrome_lists(text: str) -> tuple[list[str], list[str]]:
    """Parse the two required chrome lists from a docs markdown page.

    Args:
        text: Page markdown.

    Returns:
        (on-this-page items, enables items).

    Raises:
        AssertionError: Chrome missing or empty.
    """
    on_mark = "**What's on this page**"
    en_mark = "**What this enables**"
    on_at = text.index(on_mark)
    en_at = text.index(en_mark)
    assert en_at > on_at

    def items(block: str) -> list[str]:
        found: list[str] = []
        for line in block.splitlines():
            if line.startswith("- "):
                found.append(line[2:])
            elif found and line.strip() == "":
                continue
            elif found and line.strip():
                break
        return found

    on_items = items(text[on_at + len(on_mark) : en_at])
    en_items = items(text[en_at + len(en_mark) :])
    assert on_items, "empty What's on this page list"
    assert en_items, "empty What this enables list"
    return on_items, en_items


def test_every_docs_page_chrome_wraps(brief) -> None:
    """Every docs markdown page's chrome pair wraps into one card."""
    pages = sorted(p for p in DOCS.rglob("*.md") if p.is_file())
    assert pages
    failures: list[str] = []
    for path in pages:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        try:
            on_items, en_items = _chrome_lists(text)
        except (ValueError, AssertionError) as exc:
            failures.append(f"{rel}: {exc}")
            continue
        on_ul = "<ul>" + "".join(
            f"<li>{html_lib.escape(item)}</li>" for item in on_items
        ) + "</ul>"
        en_ul = "<ul>" + "".join(
            f"<li>{html_lib.escape(item)}</li>" for item in en_items
        ) + "</ul>"
        src = (
            f"<h1>{html_lib.escape(path.stem)}</h1>"
            "<p><strong>What's on this page</strong></p>"
            f"{on_ul}"
            "<p><strong>What this enables</strong></p>"
            f"{en_ul}"
        )
        out = brief.wrap_page_brief(src)
        if 'class="ez-page-brief"' not in out:
            failures.append(f"{rel}: wrap did not emit ez-page-brief")
        elif out.count("<ul>") != src.count("<ul>"):
            failures.append(f"{rel}: list count changed")
    assert failures == [], "page-brief wrap gaps:\n" + "\n".join(failures)


def test_hooks_on_post_page_wraps_brief(hooks) -> None:
    """on_post_page wraps the pair after h1 and still glossary-wraps list text."""
    html = (
        '<html><body><article class="md-content__inner md-typeset">'
        "<h1>Hi</h1>"
        "<p><strong>What's on this page</strong></p>"
        "<ul><li>Queue in ComfyUI</li></ul>"
        "<p><strong>What this enables</strong></p>"
        "<ul><li>A first still</li></ul>"
        "</article></body></html>"
    )
    out = hooks.on_post_page(html)
    assert 'class="ez-page-brief"' in out
    assert "ez-page-brief__on-page" in out
    on_page = out[
        out.index("ez-page-brief__on-page") : out.index("ez-page-brief__enables")
    ]
    assert "Queue" in on_page
    assert "ComfyUI" in on_page
    assert 'class="ez-term"' in on_page
    brief_at = out.index('class="ez-page-brief"')
    term_at = out.index('class="ez-term"')
    assert brief_at < term_at


def test_hooks_source_calls_page_brief() -> None:
    """hooks.py loads page_brief and wraps after the chip, before glossary."""
    text = HOOKS_PY.read_text(encoding="utf-8")
    assert "wrap_page_brief" in text
    assert "page_brief" in text
    wrap_at = text.index("wrap_page_brief")
    gloss_at = text.index("apply_glossary")
    chip_at = text.index("_inject_published_chip")
    assert chip_at < wrap_at < gloss_at


def test_extra_css_styles_page_brief() -> None:
    """Card is a two-column grid that stacks at the published-chip breakpoint."""
    css = EXTRA_CSS.read_text(encoding="utf-8")
    assert re.search(
        r"\.ez-page-brief\s*\{[^}]*display:\s*grid",
        css,
        re.S,
    )
    assert re.search(
        r"\.ez-page-brief\s*\{[^}]*grid-template-columns:\s*1fr 1fr",
        css,
        re.S,
    )
    assert re.search(
        r"\.ez-page-brief\s*\{[^}]*clear:\s*both",
        css,
        re.S,
    )
    assert re.search(
        r"@media \(max-width: 44\.99em\)[\s\S]*?\.ez-page-brief\s*\{[^}]*"
        r"grid-template-columns:\s*1fr\s*;",
        css,
    )
    assert ".ez-page-brief__on-page" in css
    assert ".ez-page-brief__enables" in css
    assert ".ez-page-brief__title" in css
    assert ".ez-page-brief__icon" in css
    assert "prefers-reduced-motion" in css
    assert re.search(r"display\s*:\s*none", css) is None
    assert "display-none" in css


def test_conventions_document_page_brief() -> None:
    """Conventions keep source chrome and name the rendered card."""
    text = CONVENTIONS.read_text(encoding="utf-8")
    assert "**What's on this page**" in text
    assert "**What this enables**" in text
    assert "ez-page-brief" in text
    assert "hooks.py" in text
    assert "page_brief" in text or "page-brief" in text
