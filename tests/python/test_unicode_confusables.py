r"""Repo-wide guard: committed text files must not use confusable Unicode.

Editors (e.g. VS Code unicodeHighlight) flag characters that can be
mistaken for ASCII (en/em dashes, curly quotes, the ellipsis, arrows,
math symbols) with "could be confused with" warnings. This test keeps
git-tracked text files clean and points at the ASCII stand-in for each
offender. Both storage forms are checked: the literal character and the
`\\uXXXX` escape, which JSON and Python decoders turn back into the
confusable.

Exempt by design: untracked local files (.env, the gitignored site/
legacy build), binary/media assets, and non-punctuation content such as
accented letters in dub sample strings, CJK punctuation in sanitize
fixtures, progress-bar cells, and box-drawing banners.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Code point -> ASCII stand-in. Mirrors the chore/ascii-confusables sweep;
# extend both together.
FORBIDDEN: dict[int, str] = {
    # Dashes and minus sign.
    0x2010: "-", 0x2011: "-", 0x2012: "-", 0x2013: "-", 0x2014: "-",
    0x2015: "-", 0x2212: "-",
    # Curly quotes.
    0x02BC: "'", 0x02BB: "'", 0x2018: "'", 0x2019: "'", 0x201A: "'",
    0x201B: "'", 0x201C: '"', 0x201D: '"', 0x201E: '"', 0x201F: '"',
    # Ellipsis, bullet, middle dot.
    0x2026: "...", 0x2022: "-", 0x00B7: "-",
    # Non-plain spaces.
    0x00A0: " ", 0x2007: " ", 0x2009: " ", 0x202F: " ",
    # Math symbols.
    0x00D7: "x", 0x00F7: "div", 0x00B1: "+/-", 0x2248: "~", 0x2260: "!=",
    0x2261: "==", 0x2264: "<=", 0x2265: ">=",
    # Arrows.
    0x2190: "<-", 0x2191: "^", 0x2192: "->", 0x2193: "v", 0x2194: "<->",
    # Superscripts.
    0x00B2: "^2", 0x00B3: "^3",
}

# Fallback walk only (used when git is unavailable). Tracked-file listing
# already excludes untracked local dirs, so these mirror .gitignore intent.
_FALLBACK_SKIP_DIRS = {
    ".git", ".grok", "node_modules", ".next", "__pycache__", "out", "site",
}
_FALLBACK_SKIP_FILES = {"wordcut.js"}

# Raw "\uXXXX" escapes decode back into the confusable (JSON, Python).
_ESC_RE = re.compile(r"\\u([0-9a-fA-F]{4})")


def _tracked_files() -> list[Path]:
    """Git-tracked files under ROOT; directory walk if git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return [ROOT / name for name in result.stdout.split("\0") if name]
    except (OSError, subprocess.CalledProcessError):
        files: list[Path] = []
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            if any(part in _FALLBACK_SKIP_DIRS
                   for part in path.relative_to(ROOT).parts):
                continue
            if path.name in _FALLBACK_SKIP_FILES or path.name.startswith(".env"):
                continue
            files.append(path)
        return files


def test_no_confusable_unicode() -> None:
    offenders: list[str] = []
    for path in _tracked_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for code, stand_in in FORBIDDEN.items():
            if chr(code) in text:
                offenders.append(
                    f"{path.relative_to(ROOT)}: U+{code:04X} (use {stand_in!r})"
                )
        for match in _ESC_RE.finditer(text):
            code = int(match.group(1), 16)
            if code in FORBIDDEN:
                offenders.append(
                    f"{path.relative_to(ROOT)}: \\u{match.group(1)} "
                    f"(U+{code:04X}, use {FORBIDDEN[code]!r})"
                )
    assert not offenders, (
        "confusable unicode punctuation found:\n" + "\n".join(offenders[:25])
    )
