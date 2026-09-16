"""Custom-node frontends must ship a file banner and JSDoc on functions.

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
