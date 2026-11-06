"""Custom-node frontends must ship a file banner and typed JSDoc.

Presence is only half the rule: a `@param` without a type, or one typed
`{object}`, documents nothing. The broad-type counts below are a ratchet -
they may fall and never rise, and the companion gate
``bazelisk test //lints:js_types`` proves the annotations that do exist agree
with how the code uses them.

Hermetic: stdlib. Does not execute JavaScript or require a browser.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS_ROOT = ROOT / "custom_nodes"
FUNC_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?:export\s+)?(?:async\s+)?function\b",
    re.MULTILINE,
)
TAG_RE = re.compile(r"@(?:param|returns|return|type)\s+(?P<rest>[^\n]*)")
SIMPLE_TYPE_RE = re.compile(r"^\{(?P<type>[^{}/]+)\}")
"""A one-token JSDoc type such as ``{string}``; anything with nested braces is
an inline object literal and counts as typed without being parsed."""
BROAD_TYPES: frozenset[str] = frozenset({"object", "Object", "*", "any", "Any"})
"""JSDoc types that name no shape. Each one is debt, not documentation."""

BROAD_TYPE_BUDGET = 307
"""Highest number of broad JSDoc type expressions allowed across the frontends.

A ratchet: it falls as `{object}` params gain a real ``@typedef`` and it only
rises with a review conversation. See docs/contribute/typing.md.
"""

FILES_MISSING_TYPEDEF_BUDGET = 20
"""Highest number of frontend files allowed to declare no ``@typedef``."""


def _js_files() -> list[Path]:
    """List first-party custom-node JavaScript files.

    Returns:
        Sorted ``.js`` paths under ``custom_nodes/``.
    """
    return sorted(JS_ROOT.rglob("*.js"))


def _has_file_banner(text: str) -> bool:
    """True when the file starts with a block comment (after optional shebang).

    Args:
        text: File contents.

    Returns:
        Whether a ``/**`` banner is present near the top.
    """
    stripped = text.lstrip()
    if stripped.startswith("#!"):
        rest = stripped.split("\n", 1)
        stripped = rest[1].lstrip() if len(rest) == 2 else ""
    return stripped.startswith("/*")


def _function_missing_jsdoc(text: str) -> list[int]:
    """Line numbers of ``function`` declarations without a preceding ``/**``.

    Args:
        text: File contents.

    Returns:
        1-based line numbers.
    """
    missing: list[int] = []
    lines = text.splitlines()
    for match in FUNC_RE.finditer(text):
        lineno = text[: match.start()].count("\n") + 1
        probe = lineno - 1
        found = False
        while probe >= 1:
            raw = lines[probe - 1].strip()
            if not raw:
                probe -= 1
                continue
            if raw.endswith("*/"):
                found = True
            break
        if not found:
            missing.append(lineno)
    return missing


def _tag_lines(text: str) -> list[tuple[int, str]]:
    """Extract every JSDoc tag with the text that follows it.

    Args:
        text: File contents.

    Returns:
        ``(line, text_after_tag)`` per ``@param`` / ``@returns`` / ``@type``
        tag. A tag whose text does not open with ``{`` declared no type.
    """
    found: list[tuple[int, str]] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if "@" not in raw:
            continue
        for match in TAG_RE.finditer(raw):
            found.append((number, match.group("rest").strip()))
    return found


def _simple_type(after_tag: str) -> str | None:
    """Return a tag's one-token type, or ``None`` when it has none.

    Args:
        after_tag: The text following ``@param`` / ``@returns`` / ``@type``.

    Returns:
        The declared type for a simple ``{string}``-style tag; ``None`` when
        the tag declared nothing. An inline object literal
        (``{{ua: string}}``) reports its opening brace, which is not a broad
        type and so is never returned.
    """
    match = SIMPLE_TYPE_RE.match(after_tag)
    if match:
        return match.group("type").strip()
    return None


def test_jsdoc_tags_carry_a_type() -> None:
    """Every ``@param`` / ``@returns`` names a type in braces."""
    problems: list[str] = []
    for path in _js_files():
        rel = path.relative_to(ROOT)
        for number, after_tag in _tag_lines(path.read_text(encoding="utf-8")):
            if not after_tag.startswith("{"):
                problems.append(f"{rel}:{number}: JSDoc tag has no {{type}}")
    assert not problems, "\n".join(problems[:60])


def test_broad_jsdoc_types_stay_under_budget() -> None:
    """``{object}`` and ``{*}`` are debt, and the debt may only shrink.

    A parameter typed ``{object}`` is used as a record, so TypeScript reports
    every property read against it as an error - the shape is missing, not the
    syntax. Replace one with a ``@typedef`` and lower the budget.
    """
    hits: list[str] = []
    for path in _js_files():
        rel = path.relative_to(ROOT)
        for number, after_tag in _tag_lines(path.read_text(encoding="utf-8")):
            declared = _simple_type(after_tag)
            if declared in BROAD_TYPES:
                hits.append(f"{rel}:{number}: {{{declared}}}")
    assert len(hits) <= BROAD_TYPE_BUDGET, (
        f"{len(hits)} broad JSDoc types; the budget is {BROAD_TYPE_BUDGET}. "
        "Give the parameter a @typedef instead.\n" + "\n".join(hits[:60])
    )


def test_frontends_declare_record_typedefs() -> None:
    """Frontends name the payloads they exchange with their pack routes.

    Each file that talks to a backend route should describe those records with
    ``@typedef`` so a `{object}` param can name one. The count is a ratchet.
    """
    missing = [
        str(path.relative_to(ROOT))
        for path in _js_files()
        if "@typedef" not in path.read_text(encoding="utf-8")
    ]
    assert len(missing) <= FILES_MISSING_TYPEDEF_BUDGET, (
        f"{len(missing)} frontend files declare no @typedef; the budget is "
        f"{FILES_MISSING_TYPEDEF_BUDGET}.\n" + "\n".join(missing[:60])
    )


def test_custom_node_js_has_jsdoc() -> None:
    """Fail when a custom-node JS file lacks a banner or function JSDoc."""
    files = _js_files()
    assert files, "expected custom_nodes JS files"
    problems: list[str] = []
    for path in files:
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        if not _has_file_banner(text):
            problems.append(f"{rel}:1: missing file banner /**")
        for lineno in _function_missing_jsdoc(text):
            problems.append(f"{rel}:{lineno}: function missing JSDoc /**")
    if problems:
        preview = "\n".join(problems[:60])
        extra = "" if len(problems) <= 60 else f"\n... {len(problems)} total"
        raise AssertionError(f"{len(problems)} JSDoc gaps:\n{preview}{extra}")
