"""Klein still canvas catalog: aspect and platform presets.

Hermetic stdlib. JSON lives under ``js/formats.json`` so the frontend can
fetch the same file from WEB_DIRECTORY. Look recipes resolve against the
Cinema Rack catalog at Queue time (lazy import).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

# Catalog path, combo sentinels, Klein VAE limits, default canvas.
FORMATS_PATH = Path(__file__).resolve().parent / "js" / "formats.json"
CUSTOM_ID = "custom"
CUSTOM_LABEL = "Custom"
LOOK_NONE = "none"
DEFAULT_FORMAT_ID = "aspect_16_9_ltx"
DEFAULT_PREFIX = "ez_still_studio"
LTX_FEEDER_16_9_ID = "aspect_16_9_ltx"
LTX_FEEDER_9_16_ID = "aspect_9_16_ltx"
GENERIC_16_9_FORMAT_IDS = frozenset(
    {"aspect_16_9_draft", "aspect_16_9", "aspect_16_9_mid"}
)
GENERIC_9_16_FORMAT_IDS = frozenset({"aspect_9_16_draft", "aspect_9_16"})
GRID = 16
"""Flux.2 Klein VAE spatial multiple (matches ``ez_image.nodes.GRID``)."""
MIN_DIM = GRID
MAX_DIM = 2048
MIN_BATCH = 1
MAX_BATCH = 4
DEFAULT_BATCH = 1


@dataclass(frozen=True)
class FormatSpec:
    """One canvas preset.

    Attributes:
        id: Stable snake_case id.
        label: Combo value shown in the App.
        group: Catalog section (aspect, youtube, …).
        width: Latent width, or 0 for Custom.
        height: Latent height, or 0 for Custom.
        prefix: SaveImage filename prefix.
        hint: Enhance duration_hint framing line.
        lock: Job-specific empty-of-lettering / safe-area clause.
    """

    id: str
    label: str
    group: str
    width: int
    height: int
    prefix: str
    hint: str
    lock: str


@dataclass(frozen=True)
class FormatResult:
    """Resolved canvas for one Queue.

    Attributes:
        width: Snapped latent width.
        height: Snapped latent height.
        batch: Clamped batch size.
        hint: Enhance duration / framing string (hint + lock).
        prefix: SaveImage prefix.
        context: Optional Cinema Rack splice for Enhance context.
        format_id: Catalog id used.
        label: Combo label used.
    """

    width: int
    height: int
    batch: int
    hint: str
    prefix: str
    context: str
    format_id: str
    label: str


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


def clamp_dim(n: int) -> int:
    """Snap to the Klein ÷16 grid and clamp to ``MIN_DIM``…``MAX_DIM``.

    Args:
        n: Requested pixel count.

    Returns:
        Legal latent dimension.
    """
    value = int(n)
    if value < MIN_DIM:
        snapped = MIN_DIM
    else:
        snapped = (value // GRID) * GRID
    if snapped > MAX_DIM:
        return MAX_DIM
    return snapped


def clamp_batch(n: int) -> int:
    """Clamp batch size to ``MIN_BATCH``…``MAX_BATCH``.

    Args:
        n: Requested batch.

    Returns:
        Legal batch size.
    """
    value = int(n)
    if value < MIN_BATCH:
        return MIN_BATCH
    if value > MAX_BATCH:
        return MAX_BATCH
    return value


@lru_cache(maxsize=1)
def load_formats() -> tuple[FormatSpec, ...]:
    """Load the canvas catalog in file order.

    Returns:
        Format rows.

    Raises:
        ValueError: catalog missing or malformed.
    """
    if not FORMATS_PATH.is_file():
        raise ValueError(f"missing format catalog {FORMATS_PATH}")
    raw = json.loads(FORMATS_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("formats.json must be an object")
    rows = raw.get("formats")
    if not isinstance(rows, list) or not rows:
        raise ValueError("formats.json formats must be a nonempty list")
    out: list[FormatSpec] = []
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("formats.json entries must be objects")
        spec = FormatSpec(
            id=str(item.get("id") or "").strip(),
            label=str(item.get("label") or "").strip(),
            group=str(item.get("group") or "").strip(),
            width=int(item.get("width") or 0),
            height=int(item.get("height") or 0),
            prefix=str(item.get("prefix") or DEFAULT_PREFIX).strip() or DEFAULT_PREFIX,
            hint=str(item.get("hint") or "").strip(),
            lock=str(item.get("lock") or "").strip(),
        )
        if not spec.id or not spec.label:
            raise ValueError("format row needs id and label")
        out.append(spec)
    return tuple(out)


def default_format_id() -> str:
    """Return the catalog default format id.

    Returns:
        Id from JSON ``default_id``, or ``DEFAULT_FORMAT_ID``.
    """
    raw = json.loads(FORMATS_PATH.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        value = str(raw.get("default_id") or "").strip()
        if value:
            return value
    return DEFAULT_FORMAT_ID


def custom_prefix() -> str:
    """Return the SaveImage prefix used for Custom canvases.

    Returns:
        Prefix string.
    """
    raw = json.loads(FORMATS_PATH.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        value = str(raw.get("custom_prefix") or "").strip()
        if value:
            return value
    return DEFAULT_PREFIX


def format_combo_labels() -> list[str]:
    """Combo choices: catalog labels in file order.

    Returns:
        Label strings (Custom first in the JSON file).
    """
    return [row.label for row in load_formats()]


def default_format_label() -> str:
    """Label for the default format id.

    Returns:
        Combo label.
    """
    wanted = default_format_id()
    for row in load_formats():
        if row.id == wanted:
            return row.label
    return load_formats()[0].label


def get_format(value: object) -> FormatSpec:
    """Resolve a combo value to a catalog row.

    Args:
        value: Format id or label.

    Returns:
        Matching spec, or the default row when unknown. Custom when the
        value is the Custom sentinel.
    """
    raw = _as_str(value)
    rows = load_formats()
    by_id = {row.id: row for row in rows}
    if not raw:
        return by_id.get(default_format_id(), rows[0])
    folded = raw.casefold()
    if folded in {CUSTOM_ID, CUSTOM_LABEL.casefold()}:
        return by_id[CUSTOM_ID]
    if raw in by_id:
        return by_id[raw]
    for row in rows:
        if row.label.casefold() == folded:
            return row
    return by_id.get(default_format_id(), rows[0])


def ltx_clip_format_id(value: object) -> str | None:
    """Return the LTX feeder id for a generic 16:9 or 9:16 aspect.

    Custom, named platform jobs, already-feeder rows, and other aspects
    stay put (None). Used by the Free Commercial Use quality overlay.

    Args:
        value: Format id or combo label.

    Returns:
        ``aspect_16_9_ltx`` / ``aspect_9_16_ltx``, or None.
    """
    spec = get_format(value)
    if spec.id in GENERIC_16_9_FORMAT_IDS:
        return LTX_FEEDER_16_9_ID
    if spec.id in GENERIC_9_16_FORMAT_IDS:
        return LTX_FEEDER_9_16_ID
    return None


def _compose_hint(spec: FormatSpec, width: int, height: int) -> str:
    """Build the Enhance duration_hint from a spec and resolved size.

    Args:
        spec: Catalog row.
        width: Resolved width.
        height: Resolved height.

    Returns:
        Hint plus lock, joined with a period.
    """
    hint = spec.hint.strip()
    if spec.id == CUSTOM_ID:
        hint = f"Custom still {width}×{height}"
    lock = spec.lock.strip()
    parts = [part for part in (hint, lock) if part]
    return ". ".join(parts)


def _cinema_recipes() -> Mapping[str, Any] | None:
    """Load Cinema Rack recipes, or None when the pack is missing.

    Returns:
        Recipe id → object mapping, or None.
    """
    try:
        from ez_prompt_enhance.cinema import load_recipes
    except Exception:  # noqa: BLE001 — hermetic tests without the pack
        return None
    return load_recipes()


def _cinema_splice(recipe_id: str) -> str:
    """Splice one recipe as Klein still language.

    Args:
        recipe_id: Cinema Rack recipe id.

    Returns:
        Splice text, or empty when cinema is missing.
    """
    try:
        from ez_prompt_enhance.cinema import (
            FLAVOR_KLEIN,
            NONE,
            WIDGET_AXIS_ORDER,
            splice,
        )
    except Exception:  # noqa: BLE001 — fail-soft without cinema
        return ""
    picks = {axis: NONE for axis in WIDGET_AXIS_ORDER}
    result = splice(picks, flavor=FLAVOR_KLEIN, recipe=recipe_id)
    return (result.text or "").strip()


def look_combo_labels() -> list[str]:
    """Combo choices for Look recipe: none first, then Cinema Rack labels.

    Returns:
        Combo strings. ``none`` only when the cinema pack is missing.
    """
    labels = [LOOK_NONE]
    recipes = _cinema_recipes()
    if recipes is None:
        return labels
    for recipe in recipes.values():
        if not isinstance(recipe, Mapping):
            continue
        label = str(recipe.get("label") or recipe.get("id") or "").strip()
        if label and label.casefold() != LOOK_NONE and label not in labels:
            labels.append(label)
    return labels


def resolve_look(value: object) -> str:
    """Return a Cinema Rack recipe id, or ``none``.

    Args:
        value: Recipe id, label, or empty.

    Returns:
        Recipe id or ``none``.
    """
    raw = _as_str(value)
    if not raw or raw.casefold() == LOOK_NONE:
        return LOOK_NONE
    recipes = _cinema_recipes()
    if recipes is None:
        return LOOK_NONE
    if raw in recipes:
        return raw
    folded = raw.casefold()
    for rid, recipe in recipes.items():
        if not isinstance(recipe, Mapping):
            continue
        label = str(recipe.get("label") or "").strip()
        if label.casefold() == folded:
            return rid
    return LOOK_NONE


def splice_look(value: object) -> str:
    """Splice a Cinema Rack recipe as Klein still context, or empty.

    Args:
        value: Look combo value.

    Returns:
        Splice text, or empty when look is none/unknown.
    """
    recipe_id = resolve_look(value)
    if recipe_id == LOOK_NONE:
        return ""
    return _cinema_splice(recipe_id)


def resolve_canvas(
    format_value: object,
    *,
    width: object = 0,
    height: object = 0,
    batch: object = DEFAULT_BATCH,
    look: object = LOOK_NONE,
) -> FormatResult:
    """Resolve widgets to a Queue canvas.

    Args:
        format_value: Format combo (id or label).
        width: Custom width widget (used when format is Custom).
        height: Custom height widget.
        batch: Batch widget.
        look: Look recipe combo.

    Returns:
        Snapped canvas, hint, prefix, and look context.
    """
    spec = get_format(format_value)
    if spec.id == CUSTOM_ID:
        resolved_w = clamp_dim(_as_int(width, 1280))
        resolved_h = clamp_dim(_as_int(height, 704))
        prefix = custom_prefix()
    else:
        resolved_w = clamp_dim(spec.width)
        resolved_h = clamp_dim(spec.height)
        prefix = spec.prefix or custom_prefix()
    resolved_batch = clamp_batch(_as_int(batch, DEFAULT_BATCH))
    return FormatResult(
        width=resolved_w,
        height=resolved_h,
        batch=resolved_batch,
        hint=_compose_hint(spec, resolved_w, resolved_h),
        prefix=prefix,
        context=splice_look(look),
        format_id=spec.id,
        label=spec.label,
    )


def reset_format_cache_for_tests() -> None:
    """Drop the loaded catalog so tests can swap files."""
    load_formats.cache_clear()


def catalog_payload() -> dict[str, Any]:
    """Return the raw JSON object (docs / tests).

    Returns:
        Parsed formats.json mapping.
    """
    raw = json.loads(FORMATS_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("formats.json must be an object")
    return raw
