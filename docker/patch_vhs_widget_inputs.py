#!/usr/bin/env python3
"""Stop VideoHelperSuite from importing deprecated widgetInputs.js.

Background
----------
ComfyUI frontend 1.x logs::

    [DEPRECATION WARNING] Detected import of deprecated legacy API:
    /extensions/core/widgetInputs.js

when a custom-node module statically imports that path. VideoHelperSuite
``web/js/VHS.core.js`` still does::

    import { setWidgetConfig } from '../../../extensions/core/widgetInputs.js'

Lab ComfyUI v0.37.0 ships frontend 1.52.7, which exposes
``window.comfyAPI.widgetInputs.setWidgetConfig``. This rewrite replaces the
legacy import with that API and a no-op fallback. Fail-soft: missing files or
unknown revisions skip with a warning and exit 0.

Typical invocation
------------------
    python3 /opt/ez-comfy/patch_vhs_widget_inputs.py /comfy-state/ComfyUI
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from patch_common import cli_main
from patch_common import consumed_and_newline as _common_consumed_and_newline

# VHS.core.js rewrite: marker, pack paths, and legacy widgetInputs import.
MARKER = "LAB_VHS_WIDGET_INPUTS_PATCH"
PACK_REL = Path("custom_nodes") / "ComfyUI-VideoHelperSuite"
CORE_REL = PACK_REL / "web" / "js" / "VHS.core.js"
IMPORT_RE = re.compile(
    r"^import\s*\{\s*setWidgetConfig\s*\}\s*from\s*['\"][^'\"]*widgetInputs\.js['\"]\s*;?",
    re.MULTILINE,
)


def _replacement(newline: str) -> str:
    """Return the comfyAPI shim line for the given newline style.

    Args:
        newline: ``\\n`` or ``\\r\\n``.

    Returns:
        Source that binds ``setWidgetConfig`` without importing widgetInputs.js.
    """
    return (
        "const setWidgetConfig = window.comfyAPI?.widgetInputs?.setWidgetConfig"
        f" ?? (() => {{}}); // {MARKER}{newline}"
    )


def _consumed_and_newline(text: str, needle: str, idx: int) -> tuple[str, str]:
    """Return the needle plus its trailing newline, and the newline style.

    Args:
        text: File contents.
        needle: Exact substring at ``idx``.
        idx: Start of ``needle`` in ``text``.

    Returns:
        ``(consumed, newline)`` where ``consumed`` is replaced as a unit.
    """
    return _common_consumed_and_newline(text, needle, idx)


def _header_import_end(text: str) -> int:
    """Return the index after the last leading ``import`` statement.

    Blank lines between imports are included. A blank line followed by
    non-import source is left in place so the shim sits with the header.

    Args:
        text: File contents after the legacy import was removed.

    Returns:
        Byte offset to insert the shim.
    """
    pos = 0
    n = len(text)
    while pos < n:
        rest = text[pos:]
        blank = re.match(r"(?:\r\n|\n)", rest)
        if blank is not None:
            after = pos + blank.end()
            if re.match(r"import\s", text[after:]):
                pos = after
                continue
            break
        imported = re.match(r"import\s.+?(?:\r\n|\n|$)", rest)
        if imported is None:
            break
        pos += imported.end()
    return pos


def _looks_valid(text: str) -> bool:
    """Return True when the patched module still has its static imports.

    Args:
        text: Candidate VHS.core.js source.

    Returns:
        True if the shim is present, widgetInputs.js is gone, and app/api/utils
        imports remain ahead of the shim.
    """
    if MARKER not in text:
        return False
    if "widgetInputs.js" in text:
        return False
    if "scripts/app.js" not in text:
        return False
    if "scripts/api.js" not in text:
        return False
    if "scripts/utils.js" not in text:
        return False
    if "window.comfyAPI" not in text:
        return False
    shim_at = text.find("const setWidgetConfig")
    if shim_at < 0:
        return False
    if text.find("import {", 0, shim_at) < 0:
        return False
    return True


def _patch_core(path: Path) -> None:
    """Rewrite the legacy ``setWidgetConfig`` import in one VHS.core.js.

    Args:
        path: Absolute path to ``VHS.core.js``.
    """
    with path.open(encoding="utf-8", newline="") as fh:
        text = fh.read()
    if MARKER in text:
        print("[vhs-widget-inputs] already applied")
        return
    match = IMPORT_RE.search(text)
    if match is None:
        if (
            "widgetInputs.js" not in text
            and "comfyAPI" in text
            and "widgetInputs" in text
        ):
            print("[vhs-widget-inputs] already modern")
            return
        print(
            "[vhs-widget-inputs] WARNING: expected setWidgetConfig import from "
            "widgetInputs.js not found; VHS widgetInputs patch skipped "
            "(upstream change)",
            file=sys.stderr,
        )
        return
    consumed, newline = _consumed_and_newline(text, match.group(0), match.start())
    stripped = text[: match.start()] + text[match.start() + len(consumed) :]
    insert_at = _header_import_end(stripped)
    new_text = stripped[:insert_at] + _replacement(newline) + stripped[insert_at:]
    if not _looks_valid(new_text):
        print(
            "[vhs-widget-inputs] WARNING: patched file failed validity check; "
            "not writing",
            file=sys.stderr,
        )
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(new_text)
    print(f"[vhs-widget-inputs] rewrote setWidgetConfig import in {path}")


def apply_patch(root: Path) -> int:
    """Rewrite VHS.core.js under a ComfyUI root.

    Args:
        root: Path to the ComfyUI repository root (contains ``custom_nodes/``).

    Returns:
        Always ``0`` (fail-soft for entrypoints).
    """
    pack = root / PACK_REL
    if not pack.is_dir():
        print(f"[vhs-widget-inputs] skip: missing {pack}", file=sys.stderr)
        return 0
    path = root / CORE_REL
    if not path.is_file():
        print(f"[vhs-widget-inputs] skip: missing {path}", file=sys.stderr)
        return 0
    _patch_core(path)
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for container entrypoints and manual operator use.

    Args:
        argv: Optional argument vector *without* the program name. When ``None``,
            uses ``sys.argv[1:]``. First argument is the ComfyUI root.

    Returns:
        Exit code from :func:`apply_patch` (normally ``0``).
    """
    return cli_main(apply_patch, argv)


if __name__ == "__main__":
    raise SystemExit(main())
