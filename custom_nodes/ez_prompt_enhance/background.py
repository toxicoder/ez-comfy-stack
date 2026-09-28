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
    "- backdrop, ground or floor, and set dressing near the subject - with: "
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
ENTIRE_ENV_VERB = (
    "Replace the entire environment - backdrop, sky, architecture, "
    "ground or floor, and set dressing near the subject -"
)
"""Swap clause that replaces a weak 'only the background' line."""
VOXEL_TRAILER = "Voxel art, cubic voxels, limited palette."
"""Short CLIP trailer for cube / block-world reconstructions."""
RECONSTRUCT_BARE = (
    "Rebuild this photographed place as a constructed cubic block world. "
    "Same camera, horizon, and inventory. The reference is a coarse block "
    "study of that place with its people removed. Rebuild every backdrop, "
    "sky, building, tree, water, floor, and prop as large axis-aligned cubes "
    "with visible tops and sides, square faces, and a coarse texel grid. "
    "Stacked block walls, cube canopies, cube water. The scene is empty of "
    "people: no figures, no humanoid shapes, no silhouettes, no person-shaped "
    "blocks. Place or look: {place}. "
    "Empty of new lettering."
)
"""Wrapper for a bare cube / voxel phrase in background_swap (people pasted
back later by EZReinsertPeople)."""
RECONSTRUCT_PHOTO_BARE = (
    "Rebuild this photographed place as a constructed cubic block world. "
    "Same camera, horizon, and inventory. The reference is the photograph of "
    "this place, including its people. Rebuild every backdrop, sky, building, "
    "tree, water, floor, and prop as large axis-aligned cubes with visible "
    "tops and sides, square faces, and a coarse texel grid. Stacked block "
    "walls, cube canopies, cube water. Keep the people as photographed, in "
    "place and photoreal. Place or look: {place}. "
    "Empty of new lettering."
)
"""People-kept variant used when the person segmenter cannot run, so the
block world never silently deletes the people."""
REASON_PRECISE_BACKGROUND = "precise background instruction"
"""Enhance status when a full swap/edit line skips the LLM rewriter."""
REASON_PHOTO_ANCHOR = "photo-anchored block world (person mask unavailable)"
"""Enhance status when a cubic swap keeps the people because the paste cannot
run; the photo, not the people-erased study, anchors the rebuild."""

_INSTRUCTION_RE = re.compile(
    r"^\s*(keep the (main )?subject|replace (only |the entire )?the background|"
    r"replace the entire environment|edit only the environment)\b",
    re.IGNORECASE,
)
"""Regex for prompts that already name a background swap or edit."""
_ONLY_BG_RE = re.compile(
    r"replace only the background(?: and ground)?",
    re.IGNORECASE,
)
"""Weak backdrop-only phrasing to upgrade on background_swap."""
_RECONSTRUCT_RE = re.compile(
    r"\b(cubes?|cubic|voxels?|block[-\s]?world|texture-pack|texel grid|"
    r"minecraft|mojang)\b",
    re.IGNORECASE,
)
"""Needles for in-place cube / voxel reconstruction."""
_REBUILD_LEAD_RE = re.compile(
    r"^\s*rebuild this photographed place\b",
    re.IGNORECASE,
)
"""Full cubic rebuild instructions that must pass through unwrapped."""
_PEOPLE_REMOVED_SENT_RE = re.compile(
    r"The reference is a coarse block study of that place with its people "
    r"removed\.",
    re.IGNORECASE,
)
"""Sentence in a full rebuild paragraph promising a people-erased study."""
_EMPTY_PEOPLE_SENT_RE = re.compile(
    r"The scene is empty of people[^.]*\.",
    re.IGNORECASE,
)
"""Sentence in a full rebuild paragraph banning every figure."""
_PEOPLE_KEPT_SENTENCE = (
    "Keep the people as photographed, in place and photoreal."
)
"""Replacement promise when the paste cannot run and people stay in the plate."""
_TRADEMARK_RE = re.compile(r"\b(minecraft|mojang)\b", re.IGNORECASE)
"""Brand names that must not reach Klein CLIP."""
_SOURCE_STILL_RE = re.compile(r"source still:", re.IGNORECASE)
"""True when a Describe caption is already spliced onto the CLIP line."""


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


def strengthen_swap_instruction(text: object) -> str:
    """Upgrade backdrop-only wording to an entire-environment clause.

    Args:
        text: Operator prompt or sample body.

    Returns:
        Strengthened string, or stripped input when there is no weak clause.
    """
    raw = _as_str(text)
    if not raw:
        return ""
    return _ONLY_BG_RE.sub(ENTIRE_ENV_VERB, raw)


def is_reconstruction(text: object) -> bool:
    """True when ``text`` asks to rebuild the plate as cubes or voxels.

    Args:
        text: Operator prompt or sample body.

    Returns:
        Whether this is an in-place block-world reconstruction.
    """
    raw = _as_str(text)
    if not raw:
        return False
    return bool(_RECONSTRUCT_RE.search(raw))


def _scrub_block_trademarks(text: str) -> str:
    """Replace block-world brand names with the word cubic.

    Args:
        text: Operator prompt or sample body.

    Returns:
        Text with minecraft / mojang rewritten to ``cubic``.
    """
    return _TRADEMARK_RE.sub("cubic", text)


def _is_rebuild_instruction(text: str) -> bool:
    """True when ``text`` is already the full cubic rebuild paragraph.

    Args:
        text: Operator prompt or sample body.

    Returns:
        Whether the line should pass through instead of ``RECONSTRUCT_BARE``.
    """
    return bool(_REBUILD_LEAD_RE.search(text))


def splice_source_caption(text: object, caption: object = "") -> str:
    """Append a Describe caption so CLIP sees source inventory.

    No-op when ``caption`` is empty or the line already has ``Source still:``.

    Args:
        text: Wrapped CLIP instruction.
        caption: Optional EZImageDescribe STRING.

    Returns:
        Instruction with ``Source still:`` trailer, or ``text`` unchanged.
    """
    body = _as_str(text)
    cap = _as_str(caption)
    if not body or not cap:
        return body
    if _SOURCE_STILL_RE.search(body):
        return body
    return f"{body.rstrip()} Source still: {cap}"


def _with_cast(body: str, clauses: str) -> str:
    """Append cast sentences unless they are already present.

    Args:
        body: Instruction without a trailing space requirement.
        clauses: Two-sentence cast block.

    Returns:
        Body plus cast, or body unchanged.
    """
    raw = body.rstrip()
    if _already_has_cast(raw):
        return raw
    return f"{raw} {clauses}"


def _with_voxel_trailer(body: str) -> str:
    """Append the voxel CLIP trailer when cubic-voxel language is missing.

    Args:
        body: Reconstruction instruction.

    Returns:
        Body plus :data:`VOXEL_TRAILER` when needed.
    """
    raw = body.rstrip()
    if "cubic voxels" in raw.casefold():
        return raw
    return f"{raw} {VOXEL_TRAILER}"


def _with_people_kept(body: str) -> str:
    """Swap an authored rebuild paragraph to the people-kept promise.

    The people-erased-study and empty-of-people sentences are replaced so a
    photo-anchored rebuild never asks Klein to delete the people nobody can
    paste back. Other text is untouched.

    Args:
        body: Full rebuild instruction (starts with Rebuild this place).

    Returns:
        Instruction with the people sentences swapped.
    """
    raw = _PEOPLE_REMOVED_SENT_RE.sub(
        "The reference is the photograph of this place, including its people.",
        body,
    )
    raw = _EMPTY_PEOPLE_SENT_RE.sub(_PEOPLE_KEPT_SENTENCE, raw)
    return raw


def wrap_background_prompt(
    text: object, mode: str, cast: object = "", *, erase_scene: bool = True
) -> str:
    """Return a subject-lock instruction for Klein background modes.

    Bare place or edit strings become a Keep-the-subject paragraph. Lines that
    already start with Keep/Replace/Edit pass through. ``background_swap``
    upgrades "replace only the background" to the entire environment, and cube
    / voxel requests stay a reconstruction of the photographed place (never
    nested inside ``SWAP_BARE``). A line that already starts with "Rebuild this
    photographed place" passes through. Brand names minecraft and mojang are
    rewritten to cubic before CLIP. Cast clauses splice unless already present;
    reconstruction plates skip the cast entirely because the reinsert-paste
    owns the people. When ``erase_scene`` is False the segmenter cannot run, so
    the people-kept rebuild variant is used instead and nothing asks for an
    empty scene.

    Args:
        text: Place name, edit, or a full targeting sentence.
        mode: ``background_swap`` or ``background_edit``.
        cast: Compact token from EZBackgroundCast.
        erase_scene: True when the person paste will run and the study is
            people-erased; False fails closed to the photo-anchored rebuild.

    Returns:
        CLIP instruction, or empty when ``text`` is blank.
    """
    raw = _as_str(text)
    if not raw:
        return ""
    kind = (mode or "").strip().lower()
    other, crowd = parse_background_cast(cast)
    clauses = _cast_clauses(other, crowd)
    raw = _scrub_block_trademarks(raw)
    if kind == "background_swap":
        raw = strengthen_swap_instruction(raw)
        if is_reconstruction(raw):
            authored = _is_rebuild_instruction(raw) or is_background_instruction(raw)
            if not erase_scene:
                if authored:
                    body = _with_people_kept(raw)
                else:
                    body = RECONSTRUCT_PHOTO_BARE.format(place=raw)
                return _with_voxel_trailer(body)
            if authored:
                body = _with_voxel_trailer(raw)
            else:
                body = RECONSTRUCT_BARE.format(place=raw)
            return body
    if is_background_instruction(raw):
        return _with_cast(raw, clauses)
    template = EDIT_BARE if kind == "background_edit" else SWAP_BARE
    return f"{template.format(place=raw)} {clauses}"
