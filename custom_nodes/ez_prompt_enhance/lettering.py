"""Build a Klein text-swap CLIP instruction from bare lettering."""

from __future__ import annotations

import re

# Lock clause appended when the operator typed only the new string.
LETTERING_LOCK = (
    "Keep the same typeface, weight, color, size, tracking, perspective, "
    "material, lighting, and every other pixel of the image. Spell the new "
    "lettering exactly."
)
"""Glyph-lock trailer for a bare replacement string."""

# Targeting lines the operator (or a sample) already wrote.
_INSTRUCTION_RE = re.compile(
    r"^\s*replace\b",
    re.IGNORECASE,
)
_LETTERING_WITH_RE = re.compile(
    r"lettering\s+with\s*:",
    re.IGNORECASE,
)


def _as_str(value: object) -> str:
    """Coerce a widget value to a stripped string.

    Args:
        value: Combo, textarea, or None.

    Returns:
        Stripped string, or empty.
    """
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ""
    return str(value).strip()


def is_lettering_instruction(text: str) -> bool:
    """True when ``text`` already names a lettering swap.

    Args:
        text: Operator prompt or sample body.

    Returns:
        Whether the string should pass through unwrapped.
    """
    raw = _as_str(text)
    if not raw:
        return False
    if _INSTRUCTION_RE.search(raw):
        return True
    if _LETTERING_WITH_RE.search(raw):
        return True
    folded = raw.casefold()
    return "typeface" in folded and "every other pixel" in folded


def wrap_text_swap_prompt(text: object) -> str:
    """Return a glyph-lock instruction for Klein text_swap.

    Bare strings such as ``HELLO`` become a replace-and-lock paragraph.
    Lines that already start with Replace, or that name typeface lock,
    pass through.

    Args:
        text: New lettering, or a full targeting sentence.

    Returns:
        CLIP instruction, or empty when ``text`` is blank.
    """
    raw = _as_str(text)
    if not raw:
        return ""
    if is_lettering_instruction(raw):
        return raw
    return f"Replace the visible lettering with: {raw}. {LETTERING_LOCK}"
