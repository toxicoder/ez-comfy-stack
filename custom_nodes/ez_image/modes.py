"""Creator-mode catalog for the Klein image-studio App.

Hermetic stdlib. JSON lives under ``js/modes.json`` so the frontend can
fetch the same file from WEB_DIRECTORY.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .nodes import CATEGORY

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes

MODES_PATH = Path(__file__).resolve().parent / "js" / "modes.json"
"""Catalog path shared with the frontend WEB_DIRECTORY."""
DEFAULT_MODE_ID = "gen_photoreal"
"""Authored default: generate a photoreal still."""
DEFAULT_PREFIX = "ez_image_studio"
"""Fallback SaveImage prefix when a row omits prefix."""
ENHANCE_MODE_COMBO = [
    "t2i",
    "edit",
    "identity",
    "text_swap",
    "background_swap",
    "background_edit",
]
"""Klein Prompt Enhance combo; also ``EZImageMode.enhance_mode`` output type."""
ENHANCE_MODES = frozenset(ENHANCE_MODE_COMBO)
"""Klein Prompt Enhance modes this catalog may select."""
ITERATE_PREFIX = "ez_iterate"
"""SaveImage prefix while Iterate is on (text-to-image, then edit)."""
ITERATE_EDIT_LINE = (
    "Edit the reference still. Apply the prompt as the change and keep everything else."
)
"""Context line for an Iterate edit pass. No creator-mode instruction."""


@dataclass(frozen=True)
class CategorySpec:
    """One mode-category row.

    Attributes:
        id: Stable snake_case id.
        label: Combo value shown in the App.
    """

    id: str
    label: str


@dataclass(frozen=True)
class ModeSpec:
    """One creator-mode row.

    Attributes:
        id: Stable snake_case id.
        label: Combo value shown in the App.
        category: Category id.
        enhance_mode: Klein Enhance mode (``t2i`` / ``edit`` / …).
        needs_ref: How many optional stills the mode prefers (0–2).
        instruction: Splice prepended to Enhance context.
        prefix: SaveImage filename prefix.
    """

    id: str
    label: str
    category: str
    enhance_mode: str
    needs_ref: int
    instruction: str
    prefix: str


@dataclass(frozen=True)
class ModeResult:
    """Resolved creator mode for one Queue.

    Attributes:
        mode_id: Catalog id used.
        label: Combo label used.
        category_id: Category id.
        category_label: Category combo label.
        enhance_mode: Klein Enhance mode.
        prefix: SaveImage prefix.
        context: Instruction plus optional incoming look/context.
        needs_ref: Preferred reference count (never required).
    """

    mode_id: str
    label: str
    category_id: str
    category_label: str
    enhance_mode: str
    prefix: str
    context: str
    needs_ref: int


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


def _as_int(value: object, default: int) -> int:
    """Parse an INT widget, falling back to ``default``.

    Args:
        value: Widget value.
        default: Fallback when missing or invalid.

    Returns:
        Integer value.
    """
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = _as_str(value)
    if not text:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def _clamp_needs_ref(value: object) -> int:
    """Clamp a preferred-reference count to 0–2.

    Args:
        value: Catalog or widget value.

    Returns:
        0, 1, or 2.
    """
    n = _as_int(value, 0)
    if n < 0:
        return 0
    if n > 2:
        return 2
    return n


def _as_bool(value: object) -> bool:
    """Parse a Comfy BOOLEAN or yes/no string.

    Args:
        value: Bool, number, or string.

    Returns:
        Parsed flag. Unrecognized values are false.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _normalize_enhance_mode(value: object) -> str:
    """Return a legal Klein Enhance mode.

    Args:
        value: Catalog enhance_mode.

    Returns:
        One of ``ENHANCE_MODES``, default ``t2i``.
    """
    raw = _as_str(value).casefold()
    if raw in ENHANCE_MODES:
        return raw
    return "t2i"


@lru_cache(maxsize=1)
def _catalog_payload() -> dict[str, Any]:
    """Load the raw modes.json object.

    Returns:
        Parsed catalog mapping (list payloads are wrapped).

    Raises:
        ValueError: catalog missing or malformed.
    """
    if not MODES_PATH.is_file():
        raise ValueError(f"missing mode catalog {MODES_PATH}")
    raw = json.loads(MODES_PATH.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {"default_id": DEFAULT_MODE_ID, "categories": [], "modes": raw}
    if not isinstance(raw, dict):
        raise ValueError("modes.json must be an object or a list")
    return raw


def catalog_payload() -> dict[str, Any]:
    """Return the raw JSON object (docs / tests).

    Returns:
        Parsed modes.json mapping.
    """
    return dict(_catalog_payload())


@lru_cache(maxsize=1)
def load_categories() -> tuple[CategorySpec, ...]:
    """Load category rows in file order.

    Returns:
        Category specs. Derived from mode rows when the file omits them.
    """
    raw = _catalog_payload()
    rows = raw.get("categories")
    out: list[CategorySpec] = []
    seen: set[str] = set()
    if isinstance(rows, list):
        for item in rows:
            if not isinstance(item, dict):
                continue
            spec = CategorySpec(
                id=str(item.get("id") or "").strip(),
                label=str(item.get("label") or "").strip(),
            )
            if spec.id and spec.label and spec.id not in seen:
                seen.add(spec.id)
                out.append(spec)
    if out:
        return tuple(out)
    derived: list[CategorySpec] = []
    for mode in load_modes():
        if mode.category in seen:
            continue
        seen.add(mode.category)
        derived.append(
            CategorySpec(id=mode.category, label=mode.category.replace("_", " ").title())
        )
    return tuple(derived)


@lru_cache(maxsize=1)
def load_modes() -> tuple[ModeSpec, ...]:
    """Load the creator-mode catalog in file order.

    Returns:
        Mode rows.

    Raises:
        ValueError: catalog missing or malformed.
    """
    raw = _catalog_payload()
    rows = raw.get("modes")
    if not isinstance(rows, list) or not rows:
        raise ValueError("modes.json modes must be a nonempty list")
    out: list[ModeSpec] = []
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("modes.json entries must be objects")
        spec = ModeSpec(
            id=str(item.get("id") or "").strip(),
            label=str(item.get("label") or "").strip(),
            category=str(item.get("category") or "").strip(),
            enhance_mode=_normalize_enhance_mode(item.get("enhance_mode")),
            needs_ref=_clamp_needs_ref(item.get("needs_ref")),
            instruction=str(item.get("instruction") or "").strip(),
            prefix=str(item.get("prefix") or DEFAULT_PREFIX).strip() or DEFAULT_PREFIX,
        )
        if not spec.id or not spec.label or not spec.category:
            raise ValueError("mode row needs id, label, and category")
        out.append(spec)
    return tuple(out)


def default_mode_id() -> str:
    """Return the catalog default mode id.

    Returns:
        Id from JSON ``default_id``, or ``DEFAULT_MODE_ID``.
    """
    raw = _catalog_payload()
    value = str(raw.get("default_id") or "").strip()
    if value:
        return value
    return DEFAULT_MODE_ID


def category_combo_labels() -> list[str]:
    """Combo choices: category labels in file order.

    Returns:
        Label strings.
    """
    labels = [row.label for row in load_categories()]
    if labels:
        return labels
    return [row.category.replace("_", " ").title() for row in load_modes()]


def mode_combo_labels() -> list[str]:
    """Combo choices: all mode labels in file order.

    Returns:
        Label strings. Python Queue accepts any; JS filters by category.
    """
    return [row.label for row in load_modes()]


def default_mode_label() -> str:
    """Label for the default mode id.

    Returns:
        Combo label.
    """
    wanted = default_mode_id()
    for row in load_modes():
        if row.id == wanted:
            return row.label
    return load_modes()[0].label


def default_category_label() -> str:
    """Category label for the default mode.

    Returns:
        Combo label.
    """
    mode = get_mode(default_mode_id())
    return category_label(mode.category)


def category_label(category_id: str) -> str:
    """Return the combo label for a category id.

    Args:
        category_id: Catalog category id.

    Returns:
        Label, or a title-cased id when unknown.
    """
    cid = _as_str(category_id)
    rows = load_categories()
    for row in rows:
        if row.id == cid:
            return row.label
    if cid:
        return cid.replace("_", " ").title()
    if rows:
        return rows[0].label
    return "Generate"


def get_category(value: object) -> CategorySpec:
    """Resolve a combo value to a category row.

    Args:
        value: Category id or label.

    Returns:
        Matching spec, or the default mode's category when unknown.
    """
    raw = _as_str(value)
    rows = load_categories()
    if not rows:
        mode = get_mode(default_mode_id())
        return CategorySpec(id=mode.category, label=category_label(mode.category))
    by_id = {row.id: row for row in rows}
    if not raw:
        return by_id.get(get_mode(default_mode_id()).category, rows[0])
    if raw in by_id:
        return by_id[raw]
    folded = raw.casefold()
    for row in rows:
        if row.label.casefold() == folded:
            return row
    return by_id.get(get_mode(default_mode_id()).category, rows[0])


def get_mode(value: object, *, category: object = None) -> ModeSpec:
    """Resolve a combo value to a catalog row.

    Args:
        value: Mode id or label.
        category: Optional category id or label used when ``value`` is unknown.

    Returns:
        Matching spec. A valid mode wins even if it is not in ``category``.
        Unknown values fall back to the first mode in ``category``, then default.
    """
    raw = _as_str(value)
    rows = load_modes()
    by_id = {row.id: row for row in rows}
    if raw in by_id:
        return by_id[raw]
    folded = raw.casefold()
    for row in rows:
        if row.label.casefold() == folded:
            return row
    if category is not None:
        cat = get_category(category)
        for row in rows:
            if row.category == cat.id:
                return row
    return by_id.get(default_mode_id(), rows[0])


def modes_for_category(value: object) -> tuple[ModeSpec, ...]:
    """Return modes in one category, file order.

    Args:
        value: Category id or label.

    Returns:
        Matching rows (may be empty only when the catalog is empty).
    """
    cat = get_category(value)
    return tuple(row for row in load_modes() if row.category == cat.id)


def splice_mode_context(instruction: str, extra: object = "") -> str:
    """Join a mode instruction with optional incoming Enhance context.

    Args:
        instruction: Catalog instruction.
        extra: Look-recipe or other context STRING.

    Returns:
        Nonempty parts joined with a newline.
    """
    parts = [part for part in (_as_str(instruction), _as_str(extra)) if part]
    return "\n".join(parts)


def resolve_mode(
    mode_value: object,
    *,
    category: object = None,
    extra_context: object = "",
) -> ModeResult:
    """Resolve widgets to a Queue mode.

    Args:
        mode_value: Mode combo (id or label).
        category: Category combo (id or label). Used only when mode is unknown.
        extra_context: Incoming Enhance context (look splice).

    Returns:
        Instruction context, Enhance mode, and SaveImage prefix.
    """
    spec = get_mode(mode_value, category=category)
    cat_label = category_label(spec.category)
    return ModeResult(
        mode_id=spec.id,
        label=spec.label,
        category_id=spec.category,
        category_label=cat_label,
        enhance_mode=spec.enhance_mode,
        prefix=spec.prefix or DEFAULT_PREFIX,
        context=splice_mode_context(spec.instruction, extra_context),
        needs_ref=spec.needs_ref,
    )


def resolve_studio_mode(
    mode_value: object,
    *,
    category: object = None,
    extra_context: object = "",
    iterate: object = False,
    has_image: object = False,
) -> ModeResult:
    """Resolve creator mode, or the Iterate text-then-edit override.

    Iterate off is :func:`resolve_mode`. Iterate on ignores the catalog
    enhance mode, instruction, and prefix. No reference still is text-to-image.
    A present still is an edit. The look-recipe ``extra_context`` is kept.

    Args:
        mode_value: Mode combo (id or label).
        category: Category combo. Used only when mode is unknown.
        extra_context: Incoming look/context STRING.
        iterate: Iterate switch.
        has_image: True when the reference still will be attached.

    Returns:
        Instruction context, Enhance mode, and SaveImage prefix.
    """
    if not _as_bool(iterate):
        return resolve_mode(
            mode_value,
            category=category,
            extra_context=extra_context,
        )
    spec = get_mode(mode_value, category=category)
    editing = _as_bool(has_image)
    extra = _as_str(extra_context)
    if editing:
        context = splice_mode_context(ITERATE_EDIT_LINE, extra)
        enhance_mode = "edit"
        needs_ref = 1
    else:
        context = extra
        enhance_mode = "t2i"
        needs_ref = 0
    return ModeResult(
        mode_id=spec.id,
        label=spec.label,
        category_id=spec.category,
        category_label=category_label(spec.category),
        enhance_mode=enhance_mode,
        prefix=ITERATE_PREFIX,
        context=context,
        needs_ref=needs_ref,
    )


def reset_mode_cache_for_tests() -> None:
    """Drop loaded catalogs so tests can swap files."""
    _catalog_payload.cache_clear()
    load_categories.cache_clear()
    load_modes.cache_clear()


class EZImageMode:
    """Pick a creator mode (background swap, change text, …) for image-studio."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for category and mode.

        Returns:
            Required combos plus optional incoming context.
        """
        categories = category_combo_labels()
        modes = mode_combo_labels()
        cat_default = default_category_label()
        mode_default = default_mode_label()
        if categories and cat_default not in categories:
            cat_default = categories[0]
        if modes and mode_default not in modes:
            mode_default = modes[0]
        return {
            "required": {
                "category": (categories, {"default": cat_default}),
                "mode": (modes, {"default": mode_default}),
                "iterate": ("BOOLEAN", {"default": False}),
                "run_summary": (
                    "STRING",
                    {"default": "", "multiline": True},
                ),
            },
            "optional": {
                "context": ("STRING", {"default": "", "multiline": True}),
                "has_image": ("BOOLEAN", {"default": False, "forceInput": True}),
            },
        }

    # Comfy node contract. enhance_mode is the Klein mode combo (not STRING)
    # so image-studio can wire it into EZKleinPromptEnhance.mode.
    RETURN_TYPES = ("STRING", ENHANCE_MODE_COMBO, "STRING")
    RETURN_NAMES = ("context", "enhance_mode", "prefix")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "100 creator modes for stills/image-studio. Category filters the Mode "
        "combo in the App. Queue splices the mode instruction into Enhance "
        "context, selects t2i/edit/text_swap/identity, and sets the save "
        "prefix. Optional reference stills stay optional — modes never error "
        "when empty. Iterate (off by default) forces text-to-image, then edit "
        "once a reference still is present, and ignores the creator-mode "
        "instruction. This run is a display of the values Queue will send."
    )

    def run(
        self,
        category: object,
        mode: object,
        iterate: object = False,
        run_summary: object = "",
        context: object = "",
        has_image: object = False,
    ) -> dict[str, Any]:
        """Resolve category/mode widgets, or the Iterate override.

        Args:
            category: Category combo (id or label).
            mode: Mode combo (id or label).
            iterate: When on, no reference is t2i and a reference is edit.
            run_summary: Display-only App text. Not used at Queue.
            context: Optional incoming look/context STRING.
            has_image: Presence flag from EZOptionalImage.

        Returns:
            Comfy output-node payload with spliced context, Enhance mode,
            and SaveImage prefix.
        """
        del run_summary
        result = resolve_studio_mode(
            mode,
            category=category,
            extra_context=context,
            iterate=iterate,
            has_image=has_image,
        )
        summary = f"{result.label} · {result.enhance_mode} · {result.prefix}"
        return {
            "ui": {"text": (summary,)},
            "result": (result.context, result.enhance_mode, result.prefix),
        }


NODE_CLASS_MAPPINGS: dict[str, type] = {
    "EZImageMode": EZImageMode,
}
"""Comfy class-name registry for creator-mode nodes."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZImageMode": "Creator mode",
}
"""Comfy display-name registry for creator-mode nodes."""
