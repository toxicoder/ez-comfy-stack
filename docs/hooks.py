"""MkDocs build/serve hooks for ez-comfy-stack docs.

Branch-aware site artifacts (mike aliases ``latest`` / ``development``):

- ``on_config`` sets ``edit_uri`` to the long-lived git ref for the alias
  (``edit/main/docs/`` or ``edit/development/docs/``).
- ``on_page_markdown`` rewrites this-repo GitHub ``blob``/``tree`` links so
  source links match the same ref. Optional override: ``EZ_DOCS_GIT_REF``.
- When ``MIKE_DOCS_VERSION`` or ``EZ_DOCS_VERSION`` is ``development``, injects
  a small banner so readers know they are on the development docs alias.
"""

from __future__ import annotations

import os
import re
from typing import Any

_REPO = "toxicoder/ez-comfy-stack"

_DEV_BANNER = (
    '<div class="ez-docs-dev-banner" role="status" '
    'style="margin:0.75rem 0 1rem;padding:0.65rem 0.9rem;'
    "border-left:4px solid #7c4dff;background:rgba(124,77,255,0.08);"
    'border-radius:4px;font-size:0.9rem;">'
    "<strong>Development docs</strong> — this site version tracks the "
    "<code>development</code> branch and may change without a release tag. "
    'Prefer <a href="../latest/">latest</a> for production-ready guidance.'
    "</div>"
)

_REPO_GITHUB_REF_RE = re.compile(
    rf"(https://github\.com/{re.escape(_REPO)}/"
    r"(?:blob|tree)/)"
    r"(main|master|development)"
    r"(/)",
)


def docs_version() -> str:
    """Return the active docs version alias from the environment.

    Prefers ``MIKE_DOCS_VERSION``, then ``EZ_DOCS_VERSION``. Values are
    stripped and lowercased. Empty string when unset.

    Returns:
        Docs version alias (e.g. ``development``, ``latest``) or ``""``.
    """
    return (
        os.environ.get("MIKE_DOCS_VERSION") or os.environ.get("EZ_DOCS_VERSION") or ""
    ).strip().lower()


def docs_git_ref() -> str:
    """Return the long-lived git ref for Edit links and source URLs.

    Mapping:

    - ``EZ_DOCS_GIT_REF`` override (if set) wins.
    - Docs version ``development`` → branch ``development``.
    - Otherwise (including empty/latest) → branch ``main``.

    Short-lived feature branch names are intentionally not inferred so
    unpublished edit/source links do not 404.

    Returns:
        ``main`` or ``development`` (or an explicit override value).
    """
    override = (os.environ.get("EZ_DOCS_GIT_REF") or "").strip()
    if override:
        return override
    if docs_version() == "development":
        return "development"
    return "main"


def on_config(config: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Stamp ``edit_uri`` for the active docs git ref.

    Args:
        config: MkDocs config mapping (mutated in place).
        **kwargs: Unused MkDocs hook metadata accepted for API compatibility.

    Returns:
        The same config mapping with ``edit_uri`` set to
        ``edit/<ref>/docs/``.
    """
    del kwargs
    config["edit_uri"] = f"edit/{docs_git_ref()}/docs/"
    return config


def stamp_git_ref(text: str, ref: str | None = None) -> str:
    """Rewrite this-repo GitHub blob/tree branch segments to the active ref.

    Source markdown may hardcode ``main``, ``master``, or ``development``;
    the published alias decides the final ref. Third-party GitHub URLs are
    left unchanged. Fragments and query strings are preserved because only
    the branch path segment is replaced.

    Args:
        text: Markdown or HTML content.
        ref: Optional explicit git ref; defaults to ``docs_git_ref()``.

    Returns:
        Content with branch-stamped GitHub source links for this repository.
    """
    ref = ref or docs_git_ref()
    return _REPO_GITHUB_REF_RE.sub(rf"\g<1>{ref}\g<3>", text)


def on_page_markdown(markdown: str, **kwargs: Any) -> str:
    """Rewrite this-repo GitHub blob/tree branch segments to ``docs_git_ref()``.

    Args:
        markdown: Raw page markdown before rendering.
        **kwargs: Unused MkDocs hook metadata accepted for API compatibility.

    Returns:
        Markdown with branch-stamped GitHub source links for this repository.
    """
    del kwargs
    return stamp_git_ref(markdown)


def on_post_page(output: str, **kwargs: Any) -> str:
    """Inject optional development banner and re-stamp git refs in HTML.

    Args:
        output: Rendered HTML page content from MkDocs.
        **kwargs: Unused MkDocs hook metadata accepted for API compatibility.

    Returns:
        HTML with branch stamps and, when on the development alias, a
        development banner near the start of the content.
    """
    del kwargs
    output = stamp_git_ref(output)

    if docs_version() != "development" or "ez-docs-dev-banner" in output:
        return output

    html2, n = re.subn(
        r'(<article\b[^>]*class="[^"]*md-content__inner[^"]*"[^>]*>)',
        r"\1" + _DEV_BANNER,
        output,
        count=1,
        flags=re.IGNORECASE,
    )
    if n:
        return html2

    html2, n = re.subn(
        r"(<h1\b[^>]*>)",
        _DEV_BANNER + r"\1",
        output,
        count=1,
        flags=re.IGNORECASE,
    )
    if n:
        return html2

    return output
