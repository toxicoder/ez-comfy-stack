"""Build a Klein background-swap / background-edit CLIP instruction."""

from __future__ import annotations

import re

BACKGROUND_MODES = frozenset({"background_swap", "background_edit"})
"""Klein Enhance modes that wrap a background lock."""

OTHER_ON = (
    "Treat companions and group members beside the main subject as part of "
    "the background."
)
"""Cast line when other people in the group are environment."""
OTHER_OFF = (
    "Keep companions and group members beside the main subject locked with "
    "the hero."
)
"""Cast line when companions stay with the subject."""
CROWD_ON = (
    "Treat extras, crowd, and distant figures as part of the background."
)
"""Cast line when extras are environment."""
CROWD_OFF = "Keep extras, crowd, and distant figures as they appear."
"""Cast line when extras stay as photographed."""

SWAP_BARE = (
    "Keep the main subject from the reference. Replace the entire environment "
    "— backdrop, ground or floor, and set dressing near the subject — with: "
    "{place}. Match ground contact, scale, and wrap light. Do not invent a "
    "new hero. Empty of new lettering."
)
"""Wrapper for a bare place name in background_swap."""
EDIT_BARE = (
    "Keep the main subject from the reference. Edit only the environment as "
    "prompted: {place}. Extreme restyle, cartoon, add, or remove of backdrop, "
    "ground, and nearby set dressing is allowed. Do not change the subject's "
    "face, body, or wardrobe unless asked. Do not invent a new hero. Empty of "
    "new lettering unless asked."
)
"""Wrapper for a bare edit in background_edit."""

_INSTRUCTION_RE = re.compile(
    r"^\s*(keep the (main )?subject|replace (only |the entire )?the background|"
    r"replace the entire environment|edit only the environment)\b",
    re.IGNORECASE,
)
"""Regex for prompts that already name a background swap or edit."""


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


def _as_bool(value: object, default: bool = True) -> bool:
    """Parse a Comfy BOOLEAN or token.

    Args:
        value: Bool, number, or yes/no string.
        default: Result when ``value`` is None.

    Returns:
        Parsed flag; unrecognized strings are False.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def parse_background_cast(value: object) -> tuple[bool, bool]:
    """Return ``(other_characters, background_characters)``.

    Compact tokens look like ``other=1,crowd=0``. Missing keys default on.

    Args:
        value: Cast STRING from EZBackgroundCast, or empty.

    Returns:
        Other-characters flag, then background-characters flag.
    """
    raw = _as_str(value)
    if not raw:
        return True, True
    other = True
    crowd = True
    for part in raw.replace(";", ",").split(","):
        item = part.strip().lower()
        if not item or "=" not in item:
            continue
        key, _, rest = item.partition("=")
        flag = rest.strip() in {"1", "true", "yes", "on"}
        name = key.strip()
        if name in {"other", "other_characters"}:
            other = flag
        elif name in {"crowd", "background", "background_characters"}:
            crowd = flag
    return other, crowd


def format_background_cast(
    *,
    other_characters: object = True,
    background_characters: object = True,
) -> str:
    """Serialize the two BOOLEAN widgets to a compact cast token.

    Args:
        other_characters: Companions count as background when true.
        background_characters: Extras count as background when true.

    Returns:
        ``other=1,crowd=1`` style token.
    """
    other = _as_bool(other_characters, True)
    crowd = _as_bool(background_characters, True)
    return f"other={int(other)},crowd={int(crowd)}"


def is_background_instruction(text: str) -> bool:
    """True when ``text`` already names a background swap or edit.

    Args:
        text: Operator prompt or sample body.

    Returns:
        Whether the string should pass through unwrapped (cast may still splice).
    """
    raw = _as_str(text)
    if not raw:
        return False
    return bool(_INSTRUCTION_RE.search(raw))


def _cast_clauses(other: bool, crowd: bool) -> str:
    """Join the two character-lock sentences.

    Args:
        other: Treat companions as background when true.
        crowd: Treat extras as background when true.

    Returns:
        Two sentences separated by a space.
    """
    other_line = OTHER_ON if other else OTHER_OFF
    crowd_line = CROWD_ON if crowd else CROWD_OFF
    return f"{other_line} {crowd_line}"


def _already_has_cast(text: str) -> bool:
    """True when the prompt already names companion or extra lock.

    Args:
        text: Instruction body.

    Returns:
        Whether cast clauses are already present.
    """
    folded = text.casefold()
    return "companions and group members" in folded or "extras, crowd" in folded


def wrap_background_prompt(text: object, mode: str, cast: object = "") -> str:
    """Return a subject-lock instruction for Klein background modes.

    Bare place or edit strings become a Keep-the-subject paragraph. Lines that
    already start with Keep/Replace/Edit pass through. Cast clauses always
    splice unless they are already present.

    Args:
        text: Place name, edit, or a full targeting sentence.
        mode: ``background_swap`` or ``background_edit``.
        cast: Compact token from EZBackgroundCast.

    Returns:
        CLIP instruction, or empty when ``text`` is blank.
    """
    raw = _as_str(text)
    if not raw:
        return ""
    kind = (mode or "").strip().lower()
    other, crowd = parse_background_cast(cast)
    clauses = _cast_clauses(other, crowd)
    if is_background_instruction(raw):
        body = raw.rstrip()
        if _already_has_cast(body):
            return body
        return f"{body} {clauses}"
    template = EDIT_BARE if kind == "background_edit" else SWAP_BARE
    return f"{template.format(place=raw)} {clauses}"
