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
- ``on_post_page`` injects a site-wide last-published chip from
  ``EZ_DOCS_PUBLISHED_AT``, then ``SOURCE_DATE_EPOCH``, then git HEAD. Invalid
  or missing stamps omit the chip (never ``datetime.now()``).
"""

from __future__ import annotations

import html
import importlib.util
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
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
_REPO_ROOT = Path(__file__).resolve().parent.parent
_UNSET = object()
_published_cache: datetime | None | object = _UNSET

_CALENDAR_SVG = (
    '<svg class="ez-published-chip__icon" xmlns="http://www.w3.org/2000/svg" '
    'viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20a2 2 0 0 0 '
    '2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2m0 16H5V10h14zM5 8V6h14v2z"></path>'
    "</svg>"
)

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


def _parse_datetime(raw: str) -> datetime | None:
    """Parse an ISO-8601 stamp or integer unix seconds as aware UTC.

    Args:
        raw: Env or git value (already stripped).

    Returns:
        Timezone-aware UTC datetime, or ``None`` when unparsable.
    """
    if not raw:
        return None
    if re.fullmatch(r"-?\d+", raw):
        try:
            return datetime.fromtimestamp(int(raw), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    iso = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _git_head_committer_date() -> datetime | None:
    """Return git HEAD committer date for this repository, if available.

    Returns:
        Aware UTC datetime from ``%cI``, or ``None`` on any git failure.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "log", "-1", "--format=%cI"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return _parse_datetime(proc.stdout.strip())


def published_at() -> datetime | None:
    """Return the site-wide docs publish stamp for this build.

    Resolution order (cached for the process):

    1. ``EZ_DOCS_PUBLISHED_AT`` (ISO-8601 or unix seconds). A set but invalid
       value skips later fallbacks so a typo cannot silently show git HEAD.
    2. ``SOURCE_DATE_EPOCH`` (unix seconds).
    3. Git HEAD committer date.
    4. ``None`` — callers omit the chip. Never uses wall-clock now.

    Returns:
        Aware UTC datetime, or ``None`` when no stamp can be resolved.
    """
    global _published_cache
    if _published_cache is not _UNSET:
        return _published_cache if isinstance(_published_cache, datetime) else None

    env_raw = os.environ.get("EZ_DOCS_PUBLISHED_AT")
    if env_raw is not None and env_raw.strip() != "":
        stamp = _parse_datetime(env_raw.strip())
        _published_cache = stamp
        return stamp

    epoch_raw = (os.environ.get("SOURCE_DATE_EPOCH") or "").strip()
    if epoch_raw:
        stamp = _parse_datetime(epoch_raw)
        if stamp is not None:
            _published_cache = stamp
            return stamp

    stamp = _git_head_committer_date()
    _published_cache = stamp
    return stamp


def format_published_label(stamp: datetime) -> str:
    """Return an English calendar label (no locale, no zero-padded day).

    Args:
        stamp: Aware datetime (converted to UTC).

    Returns:
        Label such as ``4 Sep 2026``.
    """
    utc = stamp.astimezone(timezone.utc)
    return f"{utc.day} {utc.strftime('%b %Y')}"


def render_published_chip(stamp: datetime) -> str:
    """Return the last-published chip HTML for ``stamp``.

    Args:
        stamp: Site-wide publish datetime.

    Returns:
        HTML for a ``ez-published-chip`` status pill.
    """
    utc = stamp.astimezone(timezone.utc)
    label = format_published_label(utc)
    iso = utc.isoformat(timespec="seconds")
    title = html.escape(f"Last published {label}, {utc.strftime('%H:%M')} UTC")
    visible = html.escape(label)
    return (
        f'<span class="ez-published-chip" role="status" title="{title}">'
        f"{_CALENDAR_SVG}"
        f'<span class="ez-published-chip__label">Last published</span>'
        f'<span class="ez-published-chip__sep" aria-hidden="true">·</span>'
        f'<time datetime="{html.escape(iso, quote=True)}">{visible}</time>'
        f"</span>"
    )


def _inject_published_chip(output: str) -> str:
    """Insert the last-published chip into article chrome when a stamp exists.

    Prefers the opening ``article.md-content__inner`` tag (same region as the
    development banner), then the first ``h1``. Skips when the chip is already
    present or ``published_at()`` is ``None``.

    Args:
        output: Rendered HTML page.

    Returns:
        HTML with at most one published chip.
    """
    if "ez-published-chip" in output:
        return output
    stamp = published_at()
    if stamp is None:
        return output
    chip = render_published_chip(stamp)
    html2, n = re.subn(
        r'(<article\b[^>]*class="[^"]*md-content__inner[^"]*"[^>]*>)',
        r"\1" + chip,
        output,
        count=1,
        flags=re.IGNORECASE,
    )
    if n:
        return html2
    html2, n = re.subn(
        r"(<h1\b[^>]*>)",
        chip + r"\1",
        output,
        count=1,
        flags=re.IGNORECASE,
    )
    return html2 if n else output


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
    """Stamp refs, inject publish chip and development banner, wrap glossary.

    Args:
        output: Rendered HTML page content from MkDocs.
        **kwargs: MkDocs hook metadata; ``page`` is used for glossary hrefs.

    Returns:
        HTML with branch stamps, optional last-published chip, optional
        development banner, and glossary term triggers plus a definition
        dialog when terms matched.
    """
    page = kwargs.get("page")
    output = stamp_docs_git_ref_placeholder(stamp_git_ref(output))
    # Chip first so the development banner prepends ahead of it.
    output = _inject_published_chip(output)

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
                r'(<span\b[^>]*class="[^"]*ez-published-chip[^"]*"[^>]*>)',
                _DEV_BANNER + r"\1",
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
