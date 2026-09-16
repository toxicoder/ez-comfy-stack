"""Deterministic cinematography splice for Cinema Rack.

Hermetic stdlib. Loads JSON catalogs from ``cinema/`` and composes Klein,
Wan, and LTX prompt clauses. No LLM.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Catalog paths, combo sentinels, flavor ids, widget axes, and lazy JSON caches.
CINEMA_DIR = Path(__file__).resolve().parent
AXES_PATH = CINEMA_DIR / "axes.json"
RECIPES_PATH = CINEMA_DIR / "recipes.json"
NONE = "none"
DEFAULT_WAN_CAMERA = "fixed camera"

# Cinema flavor ids (Klein stills, Wan silent, LTX joint AV).
FLAVOR_KLEIN = "klein"
FLAVOR_KLEIN_EDIT = "klein_edit"
FLAVOR_KLEIN_IDENTITY = "klein_identity"
FLAVOR_WAN_T2V = "wan_t2v"
FLAVOR_WAN_I2V = "wan_i2v"
FLAVOR_LTX_T2V = "ltx_t2v"
FLAVOR_LTX_I2V = "ltx_i2v"

FLAVORS = (
    FLAVOR_KLEIN,
    FLAVOR_KLEIN_EDIT,
    FLAVOR_KLEIN_IDENTITY,
    FLAVOR_WAN_T2V,
    FLAVOR_WAN_I2V,
    FLAVOR_LTX_T2V,
    FLAVOR_LTX_I2V,
)

# Operator widget order (camera family first). Splice order lives on axes.json.
WIDGET_AXIS_ORDER = (
    "framing_shot_size",
    "camera_angles",
    "camera_movement",
    "lenses_optics",
    "composition",
    "lighting",
    "color_film_look",
    "time_motion",
    "in_camera_optical",
    "editing_transitions",
    "atmosphere_weather",
    "genre_looks",
    "viral_looks",
)

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,47}$")

_AXES: dict[str, dict[str, Any]] | None = None
_CATALOGS: dict[str, list[dict[str, Any]]] | None = None
_BY_ID: dict[str, dict[str, Any]] | None = None
_RECIPES: dict[str, dict[str, Any]] | None = None


@dataclass(frozen=True)
class DroppedPick:
    """One technique dropped by conflict or flavor filter."""

    technique_id: str
    reason: str


@dataclass(frozen=True)
class SpliceResult:
    """Composed prompt plus audit trail."""

    text: str
    used: tuple[str, ...] = ()
    dropped: tuple[DroppedPick, ...] = ()
    notes: str = ""
    wan_camera: str = ""


def _collapse_spaces(text: str) -> str:
    """Fold runs of space and extra blank lines.

    Args:
        text: Raw clause text.

    Returns:
        Stripped text with compact whitespace.
    """
    cleaned = re.sub(r"[ \t]+", " ", text)
    cleaned = re.sub(r" +([,.;:])", r"\1", cleaned)
    cleaned = re.sub(r"\s+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _as_bool(value: object, default: bool = True) -> bool:
    """Parse a catalog flag.

    Args:
        value: JSON bool, number, or yes/no string.
        default: Fallback when ``value`` is None or unrecognized.

    Returns:
        Parsed boolean.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {"1", "true", "yes", "on"}:
            return True
        if cleaned in {"0", "false", "no", "off"}:
            return False
    return default


def _string_list(entry: dict[str, Any], field: str) -> list[str]:
    """Read a string or list-of-strings catalog field.

    Args:
        entry: Technique object.
        field: Key such as ``conflicts``.

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


def _load_json(path: Path) -> Any:
    """Read a UTF-8 JSON file.

    Args:
        path: Catalog path under ``cinema/``.

    Returns:
        Parsed JSON value.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def load_axes() -> dict[str, dict[str, Any]]:
    """Load axis metadata (id -> fields).

    Returns:
        Axis id to metadata mapping, file order preserved.
    """
    global _AXES
    if _AXES is None:
        raw = _load_json(AXES_PATH)
        if not isinstance(raw, dict):
            raise ValueError("axes.json must be an object")
        axes: dict[str, dict[str, Any]] = {}
        for key, value in raw.items():
            if not isinstance(value, dict):
                raise ValueError(f"axis {key} must be an object")
            axes[str(key)] = dict(value)
        _AXES = axes
    return _AXES


def axis_ids() -> tuple[str, ...]:
    """Return axis ids in widget order.

    Returns:
        The 13 Cinema Rack axis ids.
    """
    axes = load_axes()
    ordered = [aid for aid in WIDGET_AXIS_ORDER if aid in axes]
    extra = [aid for aid in axes if aid not in ordered]
    return tuple(ordered + extra)


def _catalog_path(axis_id: str) -> Path:
    """Resolve the JSON file for one axis.

    Args:
        axis_id: Axis key from ``axes.json``.

    Returns:
        Path next to this module.
    """
    meta = load_axes().get(axis_id) or {}
    filename = str(meta.get("file") or f"{axis_id}.json")
    return CINEMA_DIR / filename


def load_axis(axis_id: str) -> list[dict[str, Any]]:
    """Load one axis catalog (list of technique objects).

    Args:
        axis_id: Axis key from axes.json.

    Returns:
        Technique dicts in file order.

    Raises:
        KeyError: unknown axis.
        ValueError: catalog is not a list of objects.
    """
    if axis_id not in load_axes():
        raise KeyError(f"unknown cinema axis {axis_id!r}")
    catalogs = _ensure_catalogs()
    return catalogs[axis_id]


def _ensure_catalogs() -> dict[str, list[dict[str, Any]]]:
    """Load every axis catalog once and index techniques by id.

    Returns:
        Axis id to technique list mapping (cached).
    """
    global _CATALOGS, _BY_ID
    if _CATALOGS is not None and _BY_ID is not None:
        return _CATALOGS
    catalogs: dict[str, list[dict[str, Any]]] = {}
    by_id: dict[str, dict[str, Any]] = {}
    for axis_id, meta in load_axes().items():
        path = _catalog_path(axis_id)
        raw = _load_json(path) if path.is_file() else []
        if not isinstance(raw, list):
            raise ValueError(f"{path.name} must be a list")
        rows: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                raise ValueError(f"{path.name} entries must be objects")
            entry = dict(item)
            entry["axis"] = axis_id
            entry["_splice_order"] = int(meta.get("splice_order") or 0)
            entry["_still_mode"] = str(meta.get("still_mode") or "clause")
            entry["_i2v_include"] = bool(meta.get("i2v_include"))
            entry["_identity_include"] = bool(meta.get("identity_include"))
            entry["_wan_camera"] = bool(meta.get("wan_camera"))
            tid = str(entry.get("id") or "").strip()
            if tid:
                by_id[tid] = entry
            rows.append(entry)
        catalogs[axis_id] = rows
    _CATALOGS = catalogs
    _BY_ID = by_id
    return catalogs


def technique(technique_id: str) -> dict[str, Any] | None:
    """Return one technique by id, or None.

    Args:
        technique_id: Catalog id.

    Returns:
        Technique dict including axis metadata, or None.
    """
    _ensure_catalogs()
    assert _BY_ID is not None
    key = str(technique_id or "").strip()
    if not key or key == NONE:
        return None
    return _BY_ID.get(key)


def combo_ids(axis_id: str) -> list[str]:
    """Combo choices for one axis: none first, then catalog ids.

    Args:
        axis_id: Axis key.

    Returns:
        Combo strings.
    """
    rows = load_axis(axis_id)
    ids = [str(row.get("id") or "").strip() for row in rows]
    return [NONE, *[item for item in ids if item]]


def load_recipes() -> dict[str, dict[str, Any]]:
    """Load named starter splices.

    Returns:
        Recipe id to object mapping.
    """
    global _RECIPES
    if _RECIPES is None:
        if not RECIPES_PATH.is_file():
            _RECIPES = {}
            return _RECIPES
        raw = _load_json(RECIPES_PATH)
        if not isinstance(raw, list):
            raise ValueError("recipes.json must be a list")
        recipes: dict[str, dict[str, Any]] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            rid = str(item.get("id") or "").strip()
            if rid:
                recipes[rid] = dict(item)
        _RECIPES = recipes
    return _RECIPES


def recipe_combo_ids() -> list[str]:
    """Combo choices for recipes: none first.

    Returns:
        Recipe ids with none first.
    """
    return [NONE, *load_recipes().keys()]


def apply_recipe(recipe_id: str, picks: dict[str, str]) -> dict[str, str]:
    """Fill empty axis picks from a named recipe. Explicit picks win.

    Args:
        recipe_id: Recipe id or none.
        picks: Axis id -> technique id (may include none).

    Returns:
        New picks mapping.
    """
    out = {key: str(value or NONE).strip() or NONE for key, value in picks.items()}
    rid = str(recipe_id or "").strip()
    if not rid or rid == NONE:
        return out
    recipe = load_recipes().get(rid)
    if not recipe:
        return out
    axes = recipe.get("axes") or {}
    if not isinstance(axes, dict):
        return out
    for axis_id in axis_ids():
        current = out.get(axis_id, NONE)
        if current and current != NONE:
            continue
        fill = str(axes.get(axis_id) or "").strip()
        if fill and fill != NONE:
            out[axis_id] = fill
    return out


def reset_cinema_caches_for_tests() -> None:
    """Drop loaded catalogs so tests can swap files."""
    global _AXES, _CATALOGS, _BY_ID, _RECIPES
    _AXES = None
    _CATALOGS = None
    _BY_ID = None
    _RECIPES = None


def _normalize_pick(value: object) -> str:
    """Coerce a combo pick to a catalog id or ``none``.

    Args:
        value: Widget value.

    Returns:
        Stripped id, or ``none`` when empty.
    """
    raw = value if isinstance(value, str) else str(value or NONE)
    cleaned = raw.strip() or NONE
    return cleaned


def _is_i2v(flavor: str) -> bool:
    """True for Wan/LTX image-to-video flavors.

    Args:
        flavor: Splice flavor id.

    Returns:
        Whether the start image owns look.
    """
    return flavor in {FLAVOR_WAN_I2V, FLAVOR_LTX_I2V}


def _is_klein(flavor: str) -> bool:
    """True for Klein still / edit / identity flavors.

    Args:
        flavor: Splice flavor id.

    Returns:
        Whether this is a still-family splice.
    """
    return flavor in {FLAVOR_KLEIN, FLAVOR_KLEIN_EDIT, FLAVOR_KLEIN_IDENTITY}


def _is_identity(flavor: str) -> bool:
    """True for the camera-free Klein bible flavor.

    Args:
        flavor: Splice flavor id.

    Returns:
        Whether identity skips camera axes.
    """
    return flavor == FLAVOR_KLEIN_IDENTITY


def _is_wan(flavor: str) -> bool:
    """True for Wan T2V/I2V flavors.

    Args:
        flavor: Splice flavor id.

    Returns:
        Whether Wan camera-token rules apply.
    """
    return flavor in {FLAVOR_WAN_T2V, FLAVOR_WAN_I2V}


def _is_ltx(flavor: str) -> bool:
    """True for LTX T2V/I2V flavors.

    Args:
        flavor: Splice flavor id.

    Returns:
        Whether AV audio clauses apply.
    """
    return flavor in {FLAVOR_LTX_T2V, FLAVOR_LTX_I2V}


def _still_ok(entry: dict[str, Any]) -> bool:
    """Whether a technique may appear on Klein stills.

    Args:
        entry: Technique object.

    Returns:
        ``still_ok`` flag, default True.
    """
    return _as_bool(entry.get("still_ok"), True)


def _motion_ok(entry: dict[str, Any]) -> bool:
    """Whether a technique may appear on Wan motion splices.

    Args:
        entry: Technique object.

    Returns:
        ``motion_ok`` flag, default True.
    """
    return _as_bool(entry.get("motion_ok"), True)


def _av_ok(entry: dict[str, Any]) -> bool:
    """Whether a technique may appear on LTX AV splices.

    Args:
        entry: Technique object.

    Returns:
        ``av_ok`` flag, default True.
    """
    return _as_bool(entry.get("av_ok"), True)


def _flavor_keeps(entry: dict[str, Any], flavor: str) -> str:
    """Return empty if kept, else drop reason.

    Args:
        entry: Selected technique (with axis metadata).
        flavor: Splice flavor id.

    Returns:
        Empty string when the pick survives, otherwise an operator reason.
    """
    still_mode = str(entry.get("_still_mode") or "clause")
    if _is_identity(flavor):
        if not bool(entry.get("_identity_include")):
            return "identity skips camera and coverage"
    if _is_i2v(flavor):
        if not bool(entry.get("_i2v_include")):
            return "i2v start image owns look"
    if _is_klein(flavor):
        if still_mode == "omit":
            return "editing omitted on stills"
        if not _still_ok(entry):
            return "not a still technique"
    if flavor == FLAVOR_WAN_T2V and not _motion_ok(entry):
        return "not a motion technique"
    if flavor == FLAVOR_WAN_I2V and not _motion_ok(entry):
        return "not a motion technique"
    if _is_ltx(flavor) and not _av_ok(entry):
        return "not an AV technique"
    return ""


def _resolve_conflicts(entries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[DroppedPick]]:
    """Later splice-order wins when two picks conflict.

    Args:
        entries: Selected techniques, any order.

    Returns:
        Survivors and dropped picks.
    """
    ordered = sorted(entries, key=lambda row: int(row.get("_splice_order") or 0))
    dropped: list[DroppedPick] = []
    kept: list[dict[str, Any]] = []
    for entry in ordered:
        tid = str(entry.get("id") or "")
        conflicts = set(_string_list(entry, "conflicts"))
        losers: list[int] = []
        conflicted = False
        for idx, other in enumerate(kept):
            oid = str(other.get("id") or "")
            other_conflicts = set(_string_list(other, "conflicts"))
            if tid in other_conflicts or oid in conflicts:
                losers.append(idx)
                conflicted = True
        if conflicted:
            for idx in reversed(losers):
                loser = kept.pop(idx)
                dropped.append(
                    DroppedPick(
                        str(loser.get("id") or ""),
                        f"conflicts with {tid}",
                    )
                )
        kept.append(entry)
    return kept, dropped


def _render_clause(entry: dict[str, Any], flavor: str) -> str:
    """Pick the CLIP clause for one technique.

    Args:
        entry: Technique object.
        flavor: Splice flavor id.

    Returns:
        Still freeze text, motion clause, or empty for Wan camera axes.
    """
    still_mode = str(entry.get("_still_mode") or "clause")
    clause = str(entry.get("clause") or "").strip()
    still = str(entry.get("still") or "").strip()
    if _is_klein(flavor) and still_mode == "freeze" and still:
        return still
    if _is_wan(flavor) and bool(entry.get("_wan_camera")):
        return ""
    return clause


def _render_audio(entry: dict[str, Any], flavor: str) -> str:
    """Return the LTX audio clause, or empty on other flavors.

    Args:
        entry: Technique object.
        flavor: Splice flavor id.

    Returns:
        Audio sentence, or empty.
    """
    if not _is_ltx(flavor):
        return ""
    return str(entry.get("audio") or "").strip()


def _wan_token(entry: dict[str, Any]) -> str:
    """Wan camera verb for a camera-axis technique.

    Args:
        entry: Technique object.

    Returns:
        ``wan_token``, else the lowercased label, else empty.
    """
    token = str(entry.get("wan_token") or "").strip()
    if token:
        return token
    if bool(entry.get("_wan_camera")):
        return str(entry.get("label") or "").strip().lower()
    return ""


def _join_sentences(parts: list[str]) -> str:
    """Join clauses as sentences with terminal punctuation.

    Args:
        parts: Clause fragments in splice order.

    Returns:
        One paragraph, empty parts dropped.
    """
    sentences: list[str] = []
    for part in parts:
        text = _collapse_spaces(part)
        if not text:
            continue
        if text[-1] not in ".!?":
            text = f"{text}."
        sentences.append(text)
    return " ".join(sentences)


def splice(
    picks: dict[str, str] | None = None,
    *,
    flavor: str = FLAVOR_KLEIN,
    subject: str = "",
    recipe: str = NONE,
) -> SpliceResult:
    """Compose selected techniques into one model-native prompt string.

    Args:
        picks: Axis id -> technique id. Missing axes are none.
        flavor: klein / klein_edit / klein_identity / wan_t2v / wan_i2v /
            ltx_t2v / ltx_i2v.
        subject: Optional front-loaded subject sentence. Ignored on I2V.
        recipe: Optional named splice; fills none axes only.

    Returns:
        SpliceResult with text, used ids, dropped reasons, and notes.
    """
    flavor_key = str(flavor or FLAVOR_KLEIN).strip() or FLAVOR_KLEIN
    if flavor_key not in FLAVORS:
        flavor_key = FLAVOR_KLEIN
    raw_picks = {aid: NONE for aid in axis_ids()}
    if picks:
        for key, value in picks.items():
            if key in raw_picks:
                raw_picks[key] = _normalize_pick(value)
    raw_picks = apply_recipe(recipe, raw_picks)

    selected: list[dict[str, Any]] = []
    dropped: list[DroppedPick] = []
    for axis_id, tid in raw_picks.items():
        if not tid or tid == NONE:
            continue
        entry = technique(tid)
        if entry is None:
            dropped.append(DroppedPick(tid, "unknown technique"))
            continue
        selected.append(entry)

    kept, conflict_drops = _resolve_conflicts(selected)
    dropped.extend(conflict_drops)

    survivors: list[dict[str, Any]] = []
    for entry in kept:
        reason = _flavor_keeps(entry, flavor_key)
        if reason:
            dropped.append(DroppedPick(str(entry.get("id") or ""), reason))
            continue
        survivors.append(entry)
    survivors.sort(key=lambda row: int(row.get("_splice_order") or 0))

    parts: list[str] = []
    subject_text = (subject or "").strip()
    if subject_text and not _is_i2v(flavor_key):
        parts.append(subject_text)

    wan_camera = ""
    for entry in survivors:
        clause = _render_clause(entry, flavor_key)
        if clause:
            parts.append(clause)
        audio = _render_audio(entry, flavor_key)
        if audio:
            parts.append(audio)
        if bool(entry.get("_wan_camera")):
            wan_camera = _wan_token(entry)

    if _is_wan(flavor_key):
        if not wan_camera:
            wan_camera = DEFAULT_WAN_CAMERA
        if flavor_key == FLAVOR_WAN_I2V:
            parts.insert(0, wan_camera)
        else:
            parts.append(wan_camera)

    text = _join_sentences(parts)
    notes = "; ".join(f"{item.technique_id}: {item.reason}" for item in dropped)
    used = tuple(str(entry.get("id") or "") for entry in survivors if entry.get("id"))
    return SpliceResult(
        text=text,
        used=used,
        dropped=tuple(dropped),
        notes=notes,
        wan_camera=wan_camera if _is_wan(flavor_key) else "",
    )


def format_notes(result: SpliceResult) -> str:
    """Operator-facing one-line notes.

    Args:
        result: Splice output.

    Returns:
        Notes string, or empty.
    """
    bits: list[str] = []
    if result.wan_camera:
        bits.append(f"Wan camera: {result.wan_camera}")
    if result.notes:
        bits.append(result.notes)
    return "; ".join(bits)


def validate_id(value: str) -> bool:
    """Return True when value matches the catalog id regex.

    Args:
        value: Candidate id.

    Returns:
        Whether the id is legal.
    """
    return bool(_ID_RE.fullmatch(value or ""))
