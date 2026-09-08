"""MkDocs build/serve hooks for ez-comfy-stack docs.

Branch-aware site artifacts (mike aliases ``latest`` / ``development``):

- ``on_config`` sets ``edit_uri`` to the long-lived git ref for the alias
  (``edit/main/docs/`` or ``edit/development/docs/``).
- ``on_page_markdown`` rewrites this-repo GitHub ``blob``/``tree`` links so
  source links match the same ref. Optional override: ``EZ_DOCS_GIT_REF``.
- ``on_page_markdown`` / ``on_post_page`` also replace the operator token
  ``__DOCS_GIT_REF__`` (e.g. Setup ``git clone -b``) with that ref.
- ``on_page_markdown`` expands ``ezcmd`` fences via ``docs/commands.py`` and the
  glossary placeholder via ``docs/glossary.py``.
- ``on_post_page`` injects the command-builder JSON blob, wraps the first
  glossary term hits, and injects the definition dialog (skipped on
  ``glossary.md``).
- When ``MIKE_DOCS_VERSION`` or ``EZ_DOCS_VERSION`` is ``development``, injects
  a small banner so readers know they are on the development docs alias.
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path
from typing import Any

_GLOSSARY_MOD = None
_COMMANDS_MOD = None


def _commands_mod() -> Any:
    """Load docs/commands.py once (same directory as this hooks file).

    Returns:
        The command-builder module.
    """
    global _COMMANDS_MOD
    if _COMMANDS_MOD is None:
        path = Path(__file__).resolve().parent / "commands.py"
        spec = importlib.util.spec_from_file_location("ez_docs_commands", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load commands module from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["ez_docs_commands"] = module
        spec.loader.exec_module(module)
        _COMMANDS_MOD = module
    return _COMMANDS_MOD


def _glossary_mod() -> Any:
    """Load docs/glossary.py once (same directory as this hooks file).

    Returns:
        The glossary module.
    """
    global _GLOSSARY_MOD
    if _GLOSSARY_MOD is None:
        path = Path(__file__).resolve().parent / "glossary.py"
        spec = importlib.util.spec_from_file_location("ez_docs_glossary", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load glossary module from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["ez_docs_glossary"] = module
        spec.loader.exec_module(module)
        _GLOSSARY_MOD = module
    return _GLOSSARY_MOD

_REPO = "toxicoder/ez-comfy-stack"

# Operator docs placeholder: stamped to docs_git_ref() at build time so Setup
# (and similar) matches the published docs alias without hardcoding a branch.
DOCS_GIT_REF_PLACEHOLDER = "__DOCS_GIT_REF__"

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


def stamp_docs_git_ref_placeholder(text: str, ref: str | None = None) -> str:
    """Replace ``__DOCS_GIT_REF__`` with the active long-lived git ref.

    Use the placeholder in operator-facing docs (e.g. Setup ``git clone -b``)
    so published pages match the docs alias. Literal branch names in
    contributor workflow prose are left unchanged.

    Args:
        text: Markdown or HTML content.
        ref: Optional explicit git ref; defaults to ``docs_git_ref()``.

    Returns:
        Content with all ``__DOCS_GIT_REF__`` tokens replaced.
    """
    ref = ref or docs_git_ref()
    return text.replace(DOCS_GIT_REF_PLACEHOLDER, ref)


def on_page_markdown(markdown: str, **kwargs: Any) -> str:
    """Stamp git refs, expand ezcmd fences, then the glossary placeholder.

    Args:
        markdown: Raw page markdown before rendering.
        **kwargs: MkDocs hook metadata (unused besides API compatibility).

    Returns:
        Markdown with branch stamps, command widgets, and glossary sections.
    """
    del kwargs
    stamped = stamp_docs_git_ref_placeholder(stamp_git_ref(markdown))
    stamped = _commands_mod().expand_ezcmd(stamped)
    return _glossary_mod().render_placeholder(stamped)


def on_post_page(output: str, **kwargs: Any) -> str:
    """Stamp refs, inject the development banner, then wrap glossary terms.

    Args:
        output: Rendered HTML page content from MkDocs.
        **kwargs: MkDocs hook metadata; ``page`` is used for glossary hrefs.

    Returns:
        HTML with branch stamps, optional development banner, and glossary
        term triggers plus a definition dialog when terms matched.
    """
    page = kwargs.get("page")
    output = stamp_docs_git_ref_placeholder(stamp_git_ref(output))

    if docs_version() == "development" and "ez-docs-dev-banner" not in output:
        html2, n = re.subn(
            r'(<article\b[^>]*class="[^"]*md-content__inner[^"]*"[^>]*>)',
            r"\1" + _DEV_BANNER,
            output,
            count=1,
            flags=re.IGNORECASE,
        )
        if n:
            output = html2
        else:
            html2, n = re.subn(
                r"(<h1\b[^>]*>)",
                _DEV_BANNER + r"\1",
                output,
                count=1,
                flags=re.IGNORECASE,
            )
            if n:
                output = html2

    output = _commands_mod().inject_command_assets(output)
    return _glossary_mod().apply_glossary(output, page)
