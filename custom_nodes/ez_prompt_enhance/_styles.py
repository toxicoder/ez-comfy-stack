"""Style catalog apply/instruction helpers for prompt enhance."""

from __future__ import annotations

import json
import re
from typing import Any

# Style catalog knobs (re-exported from client).
STYLE_NONE = "none"
FLAVOR_KLEIN = "klein"
FLAVOR_KLEIN_EDIT = "klein_edit"
FLAVOR_KLEIN_IDENTITY = "klein_identity"
FLAVOR_WAN = "wan"
FLAVOR_LTX = "ltx"
_STYLE_LOOK_FIELDS = ("medium", "light", "color", "texture", "camera")
_LAB_LOOK_PHRASES = (
    "HD 3D game-engine pre-rendered cutscene still",
    "HD 3D game-engine pre-rendered cutscene",
    "3D game-engine pre-rendered cutscene still",
    "3D game-engine pre-rendered cutscene",
    "game-engine pre-rendered cutscene",
    "game-engine pre-rendered",
    "game-engine",
    "photoreal cinematic still",
    "photoreal still",
    "photoreal shot",
)
STYLE_SYSTEM_ADDENDUM = (
    "The user message contains a Visual style block. That style is the only look. "
    "Rewrite the whole prompt as that medium. Drop any other medium, 3D-render, "
    "photoreal, or lens language that fights it. Output only the CLIP prompt."
)
CONTEXT_SYSTEM_ADDENDUM = (
    "The user message may contain a Context block (bible, logline, research, "
    "or episode script). That is supporting context. Rewrite the operator "
    "prompt (or tags/lyrics) so it stays consistent with Context. Do not dump "
    "Context verbatim. On I2V, FLF, and VACE the start frame owns look — do "
    "not restate look, clothing, or architecture from Context."
)
_WEAVE_BY_FLAVOR = {
    FLAVOR_KLEIN: (
        "Front-load the subject, then state this medium in the first two sentences. "
        "Lighting next. Photographic styles may keep lens and depth of field; "
        "graphic styles replace lens-and-sensor language with surface and tool marks. "
        "Stay under 150 words including style."
    ),
    FLAVOR_KLEIN_EDIT: (
        "Restyle medium, light, and grade only. Keep identity, inventory, "
        "architecture, and counts locked."
    ),
    FLAVOR_KLEIN_IDENTITY: (
        "Keep the bible camera-free. Do not add lens, shot scale, or a camera move."
    ),
    FLAVOR_WAN: (
        "Put light and lens in Aesthetic control and the medium phrases in "
        "Stylization at the end of the paragraph. Compact, not a second scene."
    ),
    FLAVOR_LTX: (
        "Weave lighting, color palette, and surface texture into the flowing "
        "present-tense paragraph. One coherent light logic. No style trailer."
    ),
    "zimage": (
        "Front-load shot and subject, then state this medium in the first two "
        "sentences. About 80 to 250 words. Photographic styles may keep lens "
        "language; graphic styles replace it with surface and tool marks. Put "
        "cleanup constraints in the positive (unmarked surfaces), not a negative box."
    ),
}

def load_styles() -> dict[str, dict[str, Any]]:
    """Load the style catalog (id -> structured look fields).

    Returns:
        Style id to look-field mapping, file order preserved.
    """
    from . import client as _c

    if _c._STYLES is None:
        raw = json.loads(_c.STYLES_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("styles.json must be an object")
        styles: dict[str, dict[str, Any]] = {}
        for key, value in raw.items():
            if not isinstance(value, dict):
                raise ValueError(f"style {key} must be an object")
            styles[str(key)] = dict(value)
        _c._STYLES = styles
    return _c._STYLES


def style_ids() -> list[str]:
    """Combo choices: none first, then catalog ids in file order.

    Returns:
        Style ids for the Enhance style widget.
    """
    return [STYLE_NONE, *load_styles().keys()]


def _style_entry(style_id: str) -> dict[str, Any]:
    """Look up one style catalog row.

    Args:
        style_id: Catalog id or ``none``.

    Returns:
        Style object, or empty dict for none/unknown.
    """
    if style_id == STYLE_NONE:
        return {}
    return load_styles().get(style_id) or {}


def _string_list(entry: dict[str, Any], field: str) -> list[str]:
    """Read a string or list-of-strings style field.

    Args:
        entry: Style object.
        field: Key such as ``must_include``.

    Returns:
        Non-empty stripped strings.
    """
    raw = entry.get(field) or []
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text:
            out.append(text)
    return out


def style_must_include(style_id: str) -> list[str]:
    """Phrases that must appear in a restyled CLIP prompt.

    Args:
        style_id: Catalog id or ``none``.

    Returns:
        ``must_include`` strings.
    """
    return _string_list(_style_entry(style_id), "must_include")


def style_conflicts(style_id: str) -> list[str]:
    """Look language this style should replace.

    Args:
        style_id: Catalog id or ``none``.

    Returns:
        ``conflicts`` strings.
    """
    return _string_list(_style_entry(style_id), "conflicts")


def style_llm_block(style_id: str) -> str:
    """Dense look paragraph (medium through camera) for one catalog id.

    Args:
        style_id: Catalog id or ``none``.

    Returns:
        Joined look fields, or empty.
    """
    entry = _style_entry(style_id)
    parts = []
    for key in _STYLE_LOOK_FIELDS:
        text = str(entry.get(key) or "").strip()
        if text:
            parts.append(text)
    return " ".join(parts)


def style_suffix(style_id: str) -> str:
    """Optional CLIP trailer for one style.

    Args:
        style_id: Catalog id or ``none``.

    Returns:
        Suffix string, or empty.
    """
    if style_id == STYLE_NONE:
        return ""
    entry = _style_entry(style_id)
    return str(entry.get("suffix") or "").strip()


def with_style_system(system: str, style_id: str) -> str:
    """Append the dropdown-wins addendum when a style is selected.

    Args:
        system: Family system prompt.
        style_id: Catalog id or ``none``.

    Returns:
        System text, unchanged when style is none.
    """
    if style_id == STYLE_NONE:
        return system
    return f"{system.rstrip()}\n\n{STYLE_SYSTEM_ADDENDUM}"


def with_cinema_system(system: str, system_name: str = "", mode: str = "") -> str:
    """Append the Cinema Rack language block for visual families.

    Args:
        system: Family system prompt.
        system_name: Prompt file stem (``klein_t2i``, ``ace_tags``, …).
        mode: Optional node mode (``i2v``, ``iclora``, …).

    Returns:
        System text. Unchanged for ACE stems or when the addendum is empty.
    """
    from . import cinema

    addendum = cinema.cinema_language_addendum(system_name, mode)
    if not addendum:
        return system
    return f"{system.rstrip()}\n\n{addendum}"


def with_context_system(system: str, context: str) -> str:
    """Append the Context-block addendum when supporting text is present.

    Args:
        system: Family system prompt.
        context: Bible / logline / research / script.

    Returns:
        System text, unchanged when context is blank.
    """
    if not (context or "").strip():
        return system
    return f"{system.rstrip()}\n\n{CONTEXT_SYSTEM_ADDENDUM}"


def compose_context_user(prompt: str, context: str = "") -> str:
    """Build a rewriter user message with an optional Context block.

    Args:
        prompt: Operator prompt, tags, or lyrics.
        context: Bible / logline / research / script. Empty is omitted.
    Returns:
        User message. Context is a trailing labeled block.
    """
    text = (prompt or "").strip()
    ctx = (context or "").strip()
    if not ctx:
        return text
    if not text:
        return f"Context:\n{ctx}"
    return f"{text}\n\nContext:\n{ctx}"


def join_context_fields(*pairs: tuple[str, str]) -> str:
    """Pack labeled STRING fields, skipping empties.

    Args:
        pairs: (label, value) tuples in display order.
    Returns:
        ``Label:\\nvalue`` blocks separated by blank lines, or empty.
    """
    blocks: list[str] = []
    for label, value in pairs:
        text = (value or "").strip()
        if not text:
            continue
        name = (label or "").strip() or "Context"
        blocks.append(f"{name}:\n{text}")
    return "\n\n".join(blocks)


def _collapse_spaces(text: str) -> str:
    """Fold runs of space and extra blank lines.

    Args:
        text: Raw CLIP text.

    Returns:
        Stripped text with compact whitespace.
    """
    cleaned = re.sub(r"[ \t]+", " ", text)
    cleaned = re.sub(r" +([,.;:])", r"\1", cleaned)
    cleaned = re.sub(r"\s+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _drop_phrase(text: str, phrase: str) -> str:
    """Remove one case-insensitive phrase from CLIP text.

    Args:
        text: Prompt body.
        phrase: Literal to strip (ignored when shorter than 5 chars).

    Returns:
        Text with matches removed (spaces not yet collapsed).
    """
    token = (phrase or "").strip()
    if len(token) < 5:
        return text
    pattern = re.compile(re.escape(token), re.IGNORECASE)
    return pattern.sub("", text)


def _own_look_blob(style_id: str) -> str:
    """Lowercased look fields that belong to this style.

    Args:
        style_id: Catalog id.

    Returns:
        Joined medium/light/color/texture/camera plus must-include and suffix.
    """
    entry = _style_entry(style_id)
    parts = [str(entry.get(field) or "") for field in _STYLE_LOOK_FIELDS]
    parts.extend(style_must_include(style_id))
    parts.append(style_suffix(style_id))
    return " ".join(parts).lower()


def _strip_phrases(style_id: str) -> list[str]:
    """Phrases to remove so a restyle does not stack two looks.

    Args:
        style_id: Catalog id being applied.

    Returns:
        Conflict phrases, lab look cliches, and other styles' mediums, longest first.
    """
    own = _own_look_blob(style_id)
    phrases = list(style_conflicts(style_id))
    for extra in _LAB_LOOK_PHRASES:
        if extra.lower() not in own:
            phrases.append(extra)
    for sid, other in load_styles().items():
        if sid == style_id:
            continue
        head = str(other.get("medium") or "").split(".")[0].strip()
        if len(head) >= 8 and head.lower() not in own:
            phrases.append(head)
        for item in _string_list(other, "must_include"):
            if len(item) >= 8 and item.lower() not in own:
                phrases.append(item)
    phrases.sort(key=len, reverse=True)
    return phrases


def apply_style_to_prompt(text: str, style_id: str) -> str:
    """Force the dropdown style into CLIP text: strip fights, front-load medium.

    Args:
        text: Rewriter or source prompt.
        style_id: Catalog id or ``none``.
    Returns:
      text unchanged when style is none; otherwise a restyled CLIP prompt.
    """
    if style_id == STYLE_NONE:
        return text
    entry = _style_entry(style_id)
    if not entry:
        return text
    body = (text or "").strip()
    for phrase in _strip_phrases(style_id):
        body = _drop_phrase(body, phrase)
    body = _collapse_spaces(body)
    medium = str(entry.get("medium") or "").strip().rstrip(".")
    light = str(entry.get("light") or "").strip().rstrip(".")
    heads: list[str] = []
    if medium and medium.lower() not in body.lower():
        heads.append(medium)
    if light and light.lower() not in body.lower():
        heads.append(light)
    if heads:
        lead = ". ".join(heads) + "."
        body = f"{lead} {body}".strip() if body else lead
    for phrase in style_must_include(style_id):
        if phrase.lower() not in body.lower():
            body = f"{body} {phrase}." if body else f"{phrase}."
    suffix = style_suffix(style_id)
    if suffix and suffix.rstrip(".").lower() not in body.lower():
        body = f"{body} {suffix}".strip() if body else suffix
    return _collapse_spaces(body)


def ensure_style_details(text: str, style_id: str) -> str:
    """Apply the selected style to CLIP text (alias of apply_style_to_prompt).

    Args:
        text: Rewriter or source prompt.
        style_id: Catalog id or ``none``.

    Returns:
        Restyled CLIP prompt, or ``text`` when style is none.
    """
    return apply_style_to_prompt(text, style_id)


def flavor_for_system(name: str) -> str:
    """Map a system-prompt stem to a style-instruction flavor.

    Args:
        name: Prompt file stem such as ``wan_i2v``.

    Returns:
        ``klein``, ``klein_edit``, ``klein_identity``, ``wan``, ``ltx``, or ``zimage``.
    """
    if name == "klein_edit":
        return FLAVOR_KLEIN_EDIT
    if name == "klein_identity":
        return FLAVOR_KLEIN_IDENTITY
    if name.startswith("zimage"):
        return "zimage"
    if name.startswith("dreamx"):
        return FLAVOR_LTX
    if name.startswith("wan") or name.startswith("longcat"):
        return FLAVOR_WAN
    if name.startswith("ltx"):
        return FLAVOR_LTX
    return FLAVOR_KLEIN


def format_style_instruction(style_id: str, flavor: str) -> str:
    """Compose the user-message style block for the local rewriter.

    Args:
        style_id: Catalog id or ``none``.
        flavor: ``klein``, ``klein_edit``, ``wan``, or ``ltx``.
    Returns:
      Empty string when style is none or unknown; otherwise a mandatory
      instruction the 4B model should weave into the rewrite.
    """
    block = style_llm_block(style_id)
    if not block:
        return ""
    entry = _style_entry(style_id)
    conflicts = style_conflicts(style_id)
    must = style_must_include(style_id)
    weave = _WEAVE_BY_FLAVOR.get(flavor, _WEAVE_BY_FLAVOR[FLAVOR_KLEIN])
    wan_term = str(entry.get("wan_stylization") or "").strip()
    lines = [
        "Visual style (mandatory; dropdown wins):",
        block,
        (
            "The selected visual style is mandatory and wins over any medium, lighting, "
            "camera-sensor, grade, film-stock, or art-style language already in the source. "
            "Rewrite those clauses so they match this style. Do not stack two styles. "
            "Do not only append a style tag. Weave medium, light, color, and texture into "
            "the rewrite. Keep subject, action, place, inventory, duration, audio notes, "
            "and the requested camera move unless this style requires a different projection. "
            "Do not name the style id. Do not emit brand names."
        ),
        f"Weave: {weave}",
    ]
    if conflicts:
        lines.append("Replace clauses that describe: " + ", ".join(conflicts) + ".")
    if must:
        lines.append("Phrases that must appear in the output: " + "; ".join(must) + ".")
    if flavor == FLAVOR_WAN and wan_term:
        lines.append(f"Wan stylization slot: {wan_term}.")
    return "\n".join(lines)
