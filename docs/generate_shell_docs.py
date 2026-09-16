#!/usr/bin/env python3
"""Extract structured shell comments into a MkDocs CLI reference.

Scans ``scripts/manage.sh``, ``scripts/lib/*.sh``, and ``scripts/utilities/*.sh``
for lab-style markers and writes ``docs/generated/shell/reference.md``.

Markers:

- ``# ## Title`` — section
- ``# ### Title`` — subsection (nested under the previous section when possible)
- ``# @command name`` — public CLI verb
- ``# @function name`` — documented helper (explicit marker only; Google
  ``#####`` banners without ``@function`` are not scraped)

Stdlib only. Session variables stay ``${SPARK_HOST}``-style — never lab
``{{PLACEHOLDER}}``. No Bazel, TypeDoc, or kubectl examples.

Usage:
  python3 docs/generate_shell_docs.py
  python3 docs/generate_shell_docs.py --force
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
OUTPUT_DIR = REPO_ROOT / "docs" / "generated" / "shell"
OUTPUT_FILE = OUTPUT_DIR / "reference.md"

SECTION_RE = re.compile(r"^#\s*##\s+(.+)$")
SUBSECTION_RE = re.compile(r"^#\s*###\s+(.+)$")
COMMAND_RE = re.compile(r"^#\s*@command\s+(\S+)\s*$")
FUNCTION_RE = re.compile(r"^#\s*@function\s+(\S+)\s*$")
COMMENT_LINE_RE = re.compile(r"^#\s?(.*)$")
HASH_BANNER_RE = re.compile(r"^#{5,}$")
SEPARATOR_RE = re.compile(r"^(={3,}|-{3,})")

PAGE_CHROME = """---
title: Generated shell reference
description: Auto-generated manage.sh and utility reference from structured comments in scripts/.
tags: [cli, manage, generated, reference]
---

# Generated shell reference

**What's on this page**

- **Commands and helpers** extracted from `# ##`, `# @command`, and `# @function` comments
- **Usage fences** that keep session variables such as `${SPARK_HOST}` and `${MODELS_DIR}`
- **Safety notes** turned into admonitions

**What this enables**

- **Looking up** a verb next to the comment that ships in the script
- **Keeping** [manage.sh reference](../../manage-cli.md) a scan catalog while this page stays generated

> Generated from structured comments in `scripts/`. Edit the source comments and re-run
> `python3 docs/generate_shell_docs.py` (or `make docs`). Do not hand-edit this file.

"""


def _format_body(body_lines: list[str]) -> str:
    """Turn a raw comment body into Markdown.

    Wraps Usage/example lines in fenced bash, converts Safety/Warning/Note
    prefixes to admonitions, and leaves ``${VAR}`` tokens untouched.

    Args:
        body_lines: Comment body lines with leading ``#`` markers already removed.

    Returns:
        Formatted Markdown, or an empty string when there is no content.
    """
    if not body_lines:
        return ""

    text = "\n".join(body_lines).strip()
    if not text:
        return ""

    lines = text.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)

    def looks_like_code_start(s: str) -> bool:
        """Return whether a line should start a fenced bash usage block.

        Args:
            s: Single body line.

        Returns:
            True when the line looks like Usage or a shell one-liner.
        """
        s = s.strip()
        if not s:
            return False
        if s.startswith(("Usage:", "./scripts/manage.sh", "./scripts/utilities/")):
            return True
        if re.match(r"^\./[a-z]", s):
            return True
        if re.match(r"^[a-z][a-z0-9_-]+\s+(-|--) ", s):
            return True
        return False

    while i < n:
        line = lines[i]
        low = line.lower().strip()
        admon = None
        if low.startswith("safety") or "safety note" in low:
            admon = "warning"
        elif low.startswith("important"):
            admon = "important"
        elif low.startswith("warning"):
            admon = "warning"
        elif low.startswith("note:") or low == "note":
            admon = "note"

        if admon:
            block = [line]
            i += 1
            while i < n:
                nxt = lines[i]
                if not nxt.strip():
                    break
                nxt_low = nxt.strip().lower()
                if nxt_low.startswith(("safety", "important", "warning", "note")) or looks_like_code_start(
                    nxt
                ):
                    break
                block.append(nxt)
                i += 1
            out.append(f"!!! {admon}\n")
            for item in block:
                out.append("    " + item)
            out.append("")
            continue

        if looks_like_code_start(line):
            code_block = [line]
            i += 1
            while i < n:
                nxt = lines[i]
                if not nxt.strip():
                    if i + 1 < n and lines[i + 1].strip():
                        code_block.append(nxt)
                        i += 1
                        continue
                    break
                if not (
                    nxt.strip().startswith(("#", " ", "\t"))
                    or looks_like_code_start(nxt)
                    or nxt.strip().startswith(("-", "*"))
                ):
                    break
                code_block.append(nxt)
                i += 1
            if out and out[-1].strip():
                out.append("")
            out.append("```bash")
            out.extend(code_block)
            out.append("```")
            out.append("")
            continue

        if line.strip() == "```":
            line = "```text"

        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "+ ")) and out and out[-1].strip():
            out.append("")
        out.append(line)
        i += 1

    return "\n".join(out).strip()


def _collect_doc_body(lines: list[str], start: int) -> tuple[list[str], int]:
    """Collect contiguous comment lines that belong to the current marker.

    Stops on the next documentation marker. Skips Google hash banners and
    ``===`` / ``---`` separators so function banners do not leak into the page.

    Args:
        lines: Full file lines.
        start: Index of the first line after the marker.

    Returns:
        Body lines (hash prefix stripped) and the next unprocessed index.
    """
    body: list[str] = []
    j = start
    n = len(lines)
    while j < n:
        raw = lines[j]
        match = COMMENT_LINE_RE.match(raw)
        if not match:
            break
        if (
            SECTION_RE.match(raw)
            or SUBSECTION_RE.match(raw)
            or COMMAND_RE.match(raw)
            or FUNCTION_RE.match(raw)
        ):
            break
        content = match.group(1)
        stripped = content.strip()
        if HASH_BANNER_RE.match(stripped) or SEPARATOR_RE.match(stripped):
            j += 1
            continue
        # Google field labels stay as prose (Globals / Arguments / …).
        body.append(content)
        j += 1
    return body, j


def extract_from_file(path: Path) -> list[str]:
    """Extract structured documentation blocks from a shell script.

    Args:
        path: Path to a ``.sh`` file.

    Returns:
        Markdown documentation blocks.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    docs: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        match = SUBSECTION_RE.match(line)
        if match:
            title = match.group(1).strip()
            body, i = _collect_doc_body(lines, i + 1)
            formatted = _format_body(body)
            sub = f"### {title}\n\n{formatted}\n" if formatted else f"### {title}\n"
            if docs and docs[-1].startswith("## "):
                docs[-1] = docs[-1].rstrip() + "\n\n" + sub
            else:
                docs.append(sub)
            continue

        match = SECTION_RE.match(line)
        if match:
            title = match.group(1).strip()
            body, i = _collect_doc_body(lines, i + 1)
            formatted = _format_body(body)
            if formatted:
                docs.append(f"## {title}\n\n{formatted}\n")
            else:
                docs.append(f"## {title}\n")
            continue

        match = COMMAND_RE.match(line)
        if match:
            cmd = match.group(1).strip()
            body, i = _collect_doc_body(lines, i + 1)
            formatted = _format_body(body)
            heading = f"Command: {cmd}"
            if formatted:
                docs.append(f"### {heading}\n\n{formatted}\n")
            else:
                docs.append(f"### {heading}\n")
            continue

        match = FUNCTION_RE.match(line)
        if match:
            func = match.group(1).strip()
            body, i = _collect_doc_body(lines, i + 1)
            formatted = _format_body(body)
            heading = f"Function `{func}`"
            if formatted:
                docs.append(f"### {heading}\n\n{formatted}\n")
            else:
                docs.append(f"### {heading}\n")
            continue

        i += 1

    return docs


def _iter_script_files() -> list[Path]:
    """Return shell files to scan, manage.sh first then lib then utilities.

    Returns:
        Existing ``.sh`` paths under ``scripts/``.
    """
    files: list[Path] = []
    priority = [
        SCRIPTS_DIR / "manage.sh",
    ]
    for path in priority:
        if path.is_file():
            files.append(path)
    for sub in ("lib", "utilities"):
        folder = SCRIPTS_DIR / sub
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.sh")):
            if path not in files:
                files.append(path)
    return files


def _collapse_blank_lines(text: str) -> str:
    """Collapse runs of blank lines and guarantee a single trailing newline.

    Args:
        text: Markdown page text.

    Returns:
        Normalized page text.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    while "\n\n\n" in normalized:
        normalized = normalized.replace("\n\n\n", "\n\n")
    return normalized.strip() + "\n"


def render_reference(script_files: list[Path] | None = None) -> str:
    """Build the full reference Markdown (chrome + extracted blocks).

    Args:
        script_files: Override scan list (tests). Default is repo scripts.

    Returns:
        Complete page text including trailing newline.
    """
    parts: list[str] = [PAGE_CHROME.rstrip(), ""]
    found_source = False
    scan = script_files if script_files is not None else _iter_script_files()
    for path in scan:
        extracted = extract_from_file(path)
        if not extracted:
            continue
        found_source = True
        try:
            rel = path.relative_to(REPO_ROOT)
        except ValueError:
            rel = path
        parts.append(f"<!-- source: {rel.as_posix()} -->")
        parts.extend(extracted)

    if not found_source:
        parts.append(
            "_No structured comments found yet._\n\n"
            "Add `# ## Title`, `# @command name`, or `# @function name` in scripts.\n"
        )

    text = _collapse_blank_lines("\n".join(parts))
    if "{{" in text and "PLACEHOLDER" in text:
        raise ValueError("generated reference must not emit lab {{PLACEHOLDER}} tokens")
    return text


def main(argv: list[str] | None = None) -> int:
    """Generate the shell reference Markdown.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit status (always 0 on success).
    """
    parser = argparse.ArgumentParser(description="Generate docs/generated/shell/reference.md")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rewrite even when content is unchanged",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    new_content = render_reference()

    existing = ""
    if OUTPUT_FILE.exists():
        try:
            existing = OUTPUT_FILE.read_text(encoding="utf-8")
        except OSError:
            existing = ""

    if existing == new_content and not args.force:
        print(f"Shell reference is up to date: {OUTPUT_FILE}")
        return 0

    OUTPUT_FILE.write_text(new_content, encoding="utf-8")
    print(f"Generated {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
